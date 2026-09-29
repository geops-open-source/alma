delete from alma.translations where msgid like 'interlis_settings.%';

insert into alma.translations (msgid, msgstr, locale) values 
('interlis_settings.url_kbs_auszug', 'https://test-url-kbs-auszug.ch', 'de'), -- URL_Kataster (MGDM)
('interlis_settings.url_katasterauszug', 'https://demo.alma-os.ch/kbs/', 'de'), -- URL KbS-Auszug (MGDM)
('interlis_settings.url_standort', 'https://test-url-standort.ch', 'de'), -- URL Standort (MGDM)
('interlis_settings.prefix_katasterauszug', 'kbs_demo_', 'de'),
('interlis_settings.amt', 'Demoinstanz alma', 'de'), -- Zustaendige_Behoerde (MGDM) / Amt.Name (ÖREB)
('interlis_settings.amt', 'Instance de démonstration alma', 'fr'), -- Zustaendige_Behoerde (MGDM) / Amt.Name (ÖREB)
('interlis_settings.amt', 'Esempio dimostrativo alma', 'it'), -- Zustaendige_Behoerde (MGDM) / Amt.Name (ÖREB)
('interlis_settings.amt_id', '40', 'de'),
('interlis_settings.amt_kuerzel', 'demo', 'de'),
('interlis_settings.amt_url', 'https://test-amt.ch/de', 'de'), -- URL_Behoerde (MGDM) / Amt.AmtImWeb (ÖREB)
('interlis_settings.amt_url', 'https://test-amt.ch/fr', 'fr'), -- Französische URL_Behoerde (MGDM) / Amt.AmtImWeb (ÖREB)
('interlis_settings.amt_url', 'https://test-amt.ch/it', 'it'), -- Italienische URL_Behoerde (MGDM) / Amt.AmtImWeb (ÖREB)
('interlis_settings.amt_uid', '12345678', 'de'), -- UID (MGDM / ÖREB)
('interlis_settings.url_', 'demo', 'de'),
('interlis_settings.url_standort_indikator', 'xy_koordinates', 'de'), -- Standort-Indikator URL_Standort (MGDM)
('interlis_settings.parzellenverweiss', 'nein', 'de'), -- Parzellenverweis angeben (MGDM)
('interlis_settings.mapping_untersuchungsmassnahmen', 'aktuellste', 'de'), --Mapping der Untersuchungsmassnahmen (MGDM)
('interlis_settings.katastername', 'Kataster der belasteten Standorte (KbS)', 'de'), 
('interlis_settings.katastername', 'Cadastre des sites pollués (CSP)', 'fr'), -- 
('interlis_settings.katastername', 'Catasto dei siti inquinati (CSIN)', 'it'), -- 
('interlis_settings.layername','ch.demo.kataster-belasteter-standorte.oereb', 'de'),
('interlis_settings.url_verweiswms', 'https://test-wms.ch/de', 'de'), -- Darstellungsdienst.VerweisWMS (ÖREB)
('interlis_settings.url_verweiswms', 'https://test-wms.ch/fr', 'fr'), -- Darstellungsdienst.VerweisWMS FR (ÖREB)
('interlis_settings.url_verweiswms', 'https://test-wms.ch/it', 'it'), -- Darstellungsdienst.VerweisWMS IT (ÖREB)
('interlis_settings.url_rechtsvorschrift_textimweb', 'https://test-rechtsvorschrift.ch/', 'de'), -- Rechtsvorschrift.TextImWeb (ÖREB)
('interlis_settings.url_textimweb_indikator', 'standortnummer', 'de') -- Standort-Indikator für URL TextImWeb (ÖREB)
;
