odoo.define('nc_management.smi_plan_filter', function (require) {
    'use strict';

    require('web.dom_ready');

    // ── Indices des colonnes filtrables dans .smi_plan_tree ──────────
    // Nature=0, Référence=1, Direction=2, Responsable=3,
    // Date Prévue=4, Avancement%=5, Efficacité=6, État=7
    var FILTERABLE_COLS = {
        0: { label: 'Nature',    statKey: 'nature' },
        2: { label: 'Direction', statKey: 'direction' },
    };

    // ── Initialisation via MutationObserver ──────────────────────────
    var _observer = new MutationObserver(function () {
        _init();
    });
    _observer.observe(document.body, { childList: true, subtree: true });

    // Lancement initial (cas où le formulaire est déjà chargé)
    $(document).ready(function () { _init(); });

    // ── Initialise les en-têtes filtrables ───────────────────────────
    function _init() {
        $('.smi_plan_tree:not(.smi-filter-ready)').each(function () {
            var $table = $(this).addClass('smi-filter-ready');
            $table.data('smi-active-filters', {});

            $table.find('thead th').each(function (idx) {
                if (!FILTERABLE_COLS[idx]) return;
                var $th = $(this);
                $th.css('cursor', 'pointer').addClass('smi-filterable-th');
                $th.append(
                    '<span class="smi-flt-icon" style="' +
                    'display:inline-block;margin-left:5px;width:15px;height:15px;' +
                    'border-radius:3px;background:#1a2e5a;color:#fff;' +
                    'font-size:9px;line-height:15px;text-align:center;' +
                    'vertical-align:middle;font-style:normal;">▼</span>'
                );
                $th.on('click.smifilter', function (e) {
                    e.stopPropagation();
                    _openMenu($table, idx, $th);
                });
            });
        });
    }

    // ── Ouvre le menu déroulant de filtre ────────────────────────────
    function _openMenu($table, colIdx, $th) {
        // Fermer tout menu ouvert
        _closeMenu();

        // Collecter les valeurs uniques de cette colonne
        var values = [];
        $table.find('tbody tr').each(function () {
            var v = $(this).find('td').eq(colIdx).text().trim();
            if (v && values.indexOf(v) === -1) values.push(v);
        });
        if (!values.length) return;

        var filters = $table.data('smi-active-filters') || {};
        var currentVal = filters[colIdx] || null;

        var $menu = $('<div id="smi-filter-menu" style="' +
            'position:fixed;z-index:10000;background:#fff;' +
            'border:1px solid #b8cae8;border-radius:6px;' +
            'box-shadow:0 6px 18px rgba(0,0,0,.18);' +
            'min-width:190px;padding:5px 0;font-size:13px;"></div>');

        // Option "Tous"
        var $all = $('<div style="padding:8px 16px;cursor:pointer;' +
                     'color:#6c757d;border-bottom:1px solid #f0f0f0;">— Tous —</div>');
        $all.hover(
            function () { $(this).css('background', '#f0f4ff'); },
            function () { $(this).css('background', ''); }
        );
        $all.on('click', function () {
            _closeMenu();
            _applyFilter($table, colIdx, null);
        });
        $menu.append($all);

        values.forEach(function (val) {
            var isActive = (val === currentVal);
            var $item = $('<div style="padding:8px 16px;cursor:pointer;' +
                (isActive ? 'background:#e8f0fe;font-weight:bold;' : '') +
                '"></div>').text(val);
            $item.hover(
                function () { $(this).css('background', '#f0f4ff'); },
                function () { $(this).css('background', isActive ? '#e8f0fe' : ''); }
            );
            $item.on('click', function () {
                _closeMenu();
                _applyFilter($table, colIdx, val);
            });
            $menu.append($item);
        });

        // Positionner sous l'en-tête
        var off = $th.offset();
        $menu.css({ top: off.top + $th.outerHeight() + 2, left: off.left });
        $('body').append($menu);

        // Fermer au clic extérieur
        $(document).one('click.smifltclose', function () { _closeMenu(); });
    }

    function _closeMenu() {
        $('#smi-filter-menu').remove();
        $(document).off('click.smifltclose');
    }

    // ── Applique le filtre sur les lignes ────────────────────────────
    function _applyFilter($table, colIdx, value) {
        var filters = $table.data('smi-active-filters') || {};

        if (value === null || value === undefined) {
            delete filters[colIdx];
        } else {
            filters[colIdx] = value;
        }
        $table.data('smi-active-filters', filters);

        // Mettre à jour l'icône de l'en-tête
        var $th = $table.find('thead th').eq(colIdx);
        var $icon = $th.find('.smi-flt-icon');
        if (filters[colIdx]) {
            $icon.css({ background: '#d44535', fontWeight: 'bold' }).text('×');
        } else {
            $icon.css({ background: '#1a2e5a', fontWeight: 'normal' }).text('▼');
        }

        // Afficher/masquer les lignes
        $table.find('tbody tr').each(function () {
            var $row = $(this);
            var visible = true;
            $.each(filters, function (idx, val) {
                if (val && $row.find('td').eq(parseInt(idx)).text().trim() !== val) {
                    visible = false;
                    return false;
                }
            });
            $row.toggle(visible);
        });

        // Recalculer les stats
        _updateStats($table);
    }

    // ── Recalcule les stats depuis les lignes visibles ───────────────
    function _updateStats($table) {
        // Exclure la ligne vide d'Odoo (add-row n'a qu'1 cellule)
        var $rows    = $table.find('tbody tr:visible').filter(function () {
            return $(this).find('td').length > 1;
        });
        var total    = $rows.length;
        var avSum    = 0;
        var realises = 0;
        var enCours  = 0;
        var nonReal  = 0;
        var efficaces = 0;

        $rows.each(function () {
            var $tds = $(this).find('td');
            var av   = parseInt($tds.eq(5).text()) || 0;  // Avancement %
            var eff  = $tds.eq(6).text().trim().toLowerCase(); // Efficacité
            avSum += av;

            if (av >= 100) realises++;
            else if (av > 0) enCours++;
            else nonReal++;

            if (eff === 'oui') efficaces++;
        });

        var avancement  = total ? Math.round(avSum / total) : 0;
        var tauxReal    = total ? Math.round(realises  / total * 100) : 0;
        var tauxEff     = total ? Math.round(efficaces / total * 100) : 0;

        var $sheet = $table.closest('.o_form_sheet');
        _setStat($sheet, 'nb_plans_integres', total);
        _setStat($sheet, 'nb_realises',       realises);
        _setStat($sheet, 'nb_en_cours',       enCours);
        _setStat($sheet, 'nb_non_realises',   nonReal);
        _setStat($sheet, 'avancement_global', avancement);
        _setStat($sheet, 'taux_realisation',  tauxReal);
        _setStat($sheet, 'taux_efficacite',   tauxEff);
    }

    function _setStat($sheet, fieldName, value) {
        // Les champs sont des <span name="fieldName"> directs (pas d'enfant)
        // On exclut o_invisible_modifier pour cibler le champ visible
        $sheet
            .find('[name="' + fieldName + '"]:not(.o_invisible_modifier)')
            .first()
            .text(value);
    }

    return {};
});
