odoo.define('nc_management.smi_plan_filter', function (require) {
    'use strict';

    require('web.dom_ready');

    // ── Configuration par type de table ─────────────────────────────
    // avCol  : index colonne "Avancement %"
    // effCol : index colonne "Efficacité"
    var TABLE_CONFIGS = {
        // Colonnes : Nature(0) Référence(1) Direction(2) Responsable(3)
        //            Date Prévue(4) Avancement%(5) Efficacité(6) État(7)
        'smi_plan_tree': {
            filterCols: {
                0: 'Nature', 1: 'Référence', 2: 'Direction',
                3: 'Responsable', 4: 'Date Prévue',
                5: 'Avancement %', 6: 'Efficacité', 7: 'État',
            },
            avCol: 5,
            effCol: 6,
        },
        // Colonnes : Nature(0) Référence(1) Direction(2) Responsable(3)
        //            Avancement%(4) État(5) Efficacité(6)
        'smi_hist_tree': {
            filterCols: {
                0: 'Nature', 1: 'Référence', 2: 'Direction',
                3: 'Responsable', 4: 'Avancement %',
                5: 'État', 6: 'Efficacité',
            },
            avCol: 4,
            effCol: 6,
        },
        // FNC — liste autonome : checkbox(0) N°FNC(1) Date(2) Direction(3)
        //   Département(4) Service(5) Signalé par(6) Responsable(7) État(8)
        'fnc_list_tree': {
            filterCols: {
                1: 'N° FNC', 2: 'Date', 3: 'Direction',
                4: 'Département', 5: 'Service',
                6: 'Signalé par', 7: 'Responsable action', 8: 'État',
            },
            avCol: -1,
            effCol: -1,
        },
        // FAC — liste autonome : checkbox(0) N°FAC(1) Date(2) Direction(3)
        //   Réf. FNC(4) Responsable(5) État(6)
        'fac_list_tree': {
            filterCols: {
                1: 'N° FAC', 2: 'Date', 3: 'Direction',
                4: 'Réf. FNC', 5: 'Responsable', 6: 'État',
            },
            avCol: -1,
            effCol: -1,
        },
    };

    // ── Initialisation via MutationObserver ──────────────────────────
    var _observer = new MutationObserver(function () { _init(); });
    _observer.observe(document.body, { childList: true, subtree: true });
    $(document).ready(function () { _init(); });

    function _init() {
        $.each(TABLE_CONFIGS, function (cls, config) {
            $('.' + cls + ':not(.smi-filter-ready)').each(function () {
                var $table = $(this).addClass('smi-filter-ready');
                $table.data('smi-active-filters', {});
                $table.data('smi-config', config);

                $table.find('thead th').each(function (idx) {
                    if (!config.filterCols[idx]) return;
                    var $th = $(this);
                    $th.addClass('smi-filterable-th');
                    $th.on('click.smifilter', function (e) {
                        e.stopPropagation();
                        _openMenu($table, idx, $th);
                    });
                });
            });
        });
    }

    // ── Ouvre le menu déroulant de filtre ────────────────────────────
    function _openMenu($table, colIdx, $th) {
        _closeMenu();

        var values = [];
        $table.find('tbody tr').each(function () {
            var v = $(this).find('td').eq(colIdx).text().trim();
            if (v && values.indexOf(v) === -1) values.push(v);
        });
        if (!values.length) return;

        var filters    = $table.data('smi-active-filters') || {};
        var currentVal = filters[colIdx] || null;

        var $menu = $('<div id="smi-filter-menu" style="' +
            'position:fixed;z-index:10000;background:#fff;' +
            'border:1px solid #b8cae8;border-radius:6px;' +
            'box-shadow:0 6px 18px rgba(0,0,0,.18);' +
            'min-width:190px;padding:5px 0;font-size:13px;"></div>');

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

        var off = $th.offset();
        $menu.css({ top: off.top + $th.outerHeight() + 2, left: off.left });
        $('body').append($menu);

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

        var $th = $table.find('thead th').eq(colIdx);
        $th.toggleClass('smi-col-filtered', !!filters[colIdx]);

        $table.find('tbody tr').each(function () {
            var $row    = $(this);
            var visible = true;
            $.each(filters, function (idx, val) {
                if (val && $row.find('td').eq(parseInt(idx)).text().trim() !== val) {
                    visible = false;
                    return false;
                }
            });
            $row.toggle(visible);
        });

        _updateStats($table);
    }

    // ── Recalcule les stats depuis les lignes visibles ───────────────
    function _updateStats($table) {
        var config   = $table.data('smi-config') || { avCol: 5, effCol: 6 };
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
            var av   = parseInt($tds.eq(config.avCol).text()) || 0;
            var eff  = $tds.eq(config.effCol).text().trim().toLowerCase();
            avSum += av;

            if (av >= 100) realises++;
            else if (av > 0) enCours++;
            else nonReal++;

            if (eff === 'oui') efficaces++;
        });

        var avancement = total ? Math.round(avSum / total) : 0;
        var tauxReal   = total ? Math.round(realises  / total * 100) : 0;
        var tauxEff    = total ? Math.round(efficaces / total * 100) : 0;

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
        $sheet
            .find('[name="' + fieldName + '"]:not(.o_invisible_modifier)')
            .first()
            .text(value);
    }

    return {};
});
