-- ============================================================
-- MIGRATION : smi_management  →  nc_management
-- Base de données : MQE
-- Exécuter en tant que superuser PostgreSQL (psql -U postgres -d MQE)
-- ============================================================

BEGIN;

-- ============================================================
-- 1. RENOMMAGE DES TABLES POSTGRESQL
-- ============================================================

ALTER TABLE IF EXISTS smi_management_nc_type                RENAME TO nc_management_nc_type;
ALTER TABLE IF EXISTS smi_management_nonconformity          RENAME TO nc_management_nonconformity;
ALTER TABLE IF EXISTS smi_management_corrective_action      RENAME TO nc_management_corrective_action;
ALTER TABLE IF EXISTS smi_management_action_line            RENAME TO nc_management_action_line;
ALTER TABLE IF EXISTS smi_management_plan_action_smi        RENAME TO nc_management_plan_action_smi;
ALTER TABLE IF EXISTS smi_management_document_revision      RENAME TO nc_management_document_revision;
ALTER TABLE IF EXISTS smi_management_form_template          RENAME TO nc_management_form_template;
ALTER TABLE IF EXISTS smi_management_form_section           RENAME TO nc_management_form_section;
ALTER TABLE IF EXISTS smi_management_form_line              RENAME TO nc_management_form_line;
ALTER TABLE IF EXISTS smi_management_dashboard              RENAME TO nc_management_dashboard;

-- Séquences de numérotation automatique des tables
ALTER SEQUENCE IF EXISTS smi_management_nc_type_id_seq               RENAME TO nc_management_nc_type_id_seq;
ALTER SEQUENCE IF EXISTS smi_management_nonconformity_id_seq         RENAME TO nc_management_nonconformity_id_seq;
ALTER SEQUENCE IF EXISTS smi_management_corrective_action_id_seq     RENAME TO nc_management_corrective_action_id_seq;
ALTER SEQUENCE IF EXISTS smi_management_action_line_id_seq           RENAME TO nc_management_action_line_id_seq;
ALTER SEQUENCE IF EXISTS smi_management_plan_action_smi_id_seq       RENAME TO nc_management_plan_action_smi_id_seq;
ALTER SEQUENCE IF EXISTS smi_management_document_revision_id_seq     RENAME TO nc_management_document_revision_id_seq;
ALTER SEQUENCE IF EXISTS smi_management_form_template_id_seq         RENAME TO nc_management_form_template_id_seq;
ALTER SEQUENCE IF EXISTS smi_management_form_section_id_seq          RENAME TO nc_management_form_section_id_seq;
ALTER SEQUENCE IF EXISTS smi_management_form_line_id_seq             RENAME TO nc_management_form_line_id_seq;
ALTER SEQUENCE IF EXISTS smi_management_dashboard_id_seq             RENAME TO nc_management_dashboard_id_seq;

-- ============================================================
-- 2. NOM DU MODULE dans ir_module_module
-- ============================================================

UPDATE ir_module_module
   SET name = 'nc_management'
 WHERE name = 'smi_management';

-- ============================================================
-- 3. ir_model — noms de modèles
-- ============================================================

UPDATE ir_model
   SET model = replace(model, 'smi_management.', 'nc_management.')
 WHERE model LIKE 'smi_management.%';

-- ============================================================
-- 4. ir_model_fields — colonne model et colonne relation
-- ============================================================

UPDATE ir_model_fields
   SET model = replace(model, 'smi_management.', 'nc_management.')
 WHERE model LIKE 'smi_management.%';

UPDATE ir_model_fields
   SET relation = replace(relation, 'smi_management.', 'nc_management.')
 WHERE relation LIKE 'smi_management.%';

-- ============================================================
-- 5. ir_model_data — module et model
-- ============================================================

UPDATE ir_model_data
   SET module = 'nc_management'
 WHERE module = 'smi_management';

UPDATE ir_model_data
   SET model = replace(model, 'smi_management.', 'nc_management.')
 WHERE model LIKE 'smi_management.%';

-- ============================================================
-- 6. ir_act_window — res_model et src_model
-- ============================================================

UPDATE ir_act_window
   SET res_model = replace(res_model, 'smi_management.', 'nc_management.')
 WHERE res_model LIKE 'smi_management.%';

UPDATE ir_act_window
   SET src_model = replace(src_model, 'smi_management.', 'nc_management.')
 WHERE src_model LIKE 'smi_management.%';

-- ============================================================
-- 7. ir_act_report_xml — model
-- ============================================================

UPDATE ir_act_report_xml
   SET model = replace(model, 'smi_management.', 'nc_management.')
 WHERE model LIKE 'smi_management.%';

-- ============================================================
-- 8. ir_cron — model_id mis à jour via ir_model (déjà fait)
--    mais si le champ model (texte) existe aussi :
-- ============================================================

UPDATE ir_cron
   SET model = replace(model, 'smi_management.', 'nc_management.')
 WHERE model LIKE 'smi_management.%';

-- ============================================================
-- 9. ir_sequence — codes des séquences FNC et FAC
-- ============================================================

UPDATE ir_sequence
   SET code = replace(code, 'smi_management.', 'nc_management.')
 WHERE code LIKE 'smi_management.%';

-- Séquences dynamiques générées par le wizard (ex: smi_management.fnc.rec → nc_management.fnc.rec)
UPDATE ir_sequence
   SET name = replace(name, 'smi_management', 'nc_management')
 WHERE name LIKE '%smi_management%';

-- ============================================================
-- 10. mail_message — colonne model
-- ============================================================

UPDATE mail_message
   SET model = replace(model, 'smi_management.', 'nc_management.')
 WHERE model LIKE 'smi_management.%';

-- ============================================================
-- 11. mail_followers — res_model
-- ============================================================

UPDATE mail_followers
   SET res_model = replace(res_model, 'smi_management.', 'nc_management.')
 WHERE res_model LIKE 'smi_management.%';

-- ============================================================
-- 12. mail_activity — res_model
-- ============================================================

UPDATE mail_activity
   SET res_model = replace(res_model, 'smi_management.', 'nc_management.')
 WHERE res_model LIKE 'smi_management.%';

-- ============================================================
-- 13. ir_rule — model_id est une FK vers ir_model (déjà mis à jour)
--    Pas de colonne texte directe, rien à faire ici.
-- ============================================================

-- ============================================================
-- 14. ir_model_access — model_id est une FK, rien à faire.
-- ============================================================

-- ============================================================
-- 15. VÉRIFICATION FINALE
-- ============================================================

-- Ces requêtes doivent toutes retourner 0 ligne après migration :
SELECT 'ir_module_module'  AS table_name, count(*) AS reste FROM ir_module_module  WHERE name        LIKE '%smi_management%'
UNION ALL
SELECT 'ir_model',          count(*) FROM ir_model          WHERE model       LIKE '%smi_management%'
UNION ALL
SELECT 'ir_model_fields',   count(*) FROM ir_model_fields   WHERE model       LIKE '%smi_management%' OR relation LIKE '%smi_management%'
UNION ALL
SELECT 'ir_model_data',     count(*) FROM ir_model_data     WHERE module = 'smi_management' OR model LIKE '%smi_management%'
UNION ALL
SELECT 'ir_act_window',     count(*) FROM ir_act_window     WHERE res_model   LIKE '%smi_management%'
UNION ALL
SELECT 'ir_act_report_xml', count(*) FROM ir_act_report_xml WHERE model       LIKE '%smi_management%'
UNION ALL
SELECT 'ir_sequence',       count(*) FROM ir_sequence       WHERE code        LIKE '%smi_management%'
UNION ALL
SELECT 'mail_message',      count(*) FROM mail_message      WHERE model       LIKE '%smi_management%'
UNION ALL
SELECT 'mail_followers',    count(*) FROM mail_followers    WHERE res_model   LIKE '%smi_management%'
UNION ALL
SELECT 'mail_activity',     count(*) FROM mail_activity     WHERE res_model   LIKE '%smi_management%';

COMMIT;
