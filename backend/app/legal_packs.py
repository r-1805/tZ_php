from __future__ import annotations

from html import escape
from typing import Any

from .catalog import GEO_PACKS, LOCALE_PACKS
from .schemas import CompanyProfile, LegalPack

EU_GEOS = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK",
}
LEGAL_DOC_FILES = [
    "privacy-policy.php",
    "cookie-policy.php",
    "terms-of-service.php",
    "legal-notice.php",
    "disclaimer.php",
]


def _cyrillic_count(value: str) -> int:
    return sum(1 for char in value if "А" <= char <= "я" or char in {"Ё", "ё"})


def _clean_text(value: str) -> str:
    if not value or _cyrillic_count(value) == 0:
        return value
    for encoding in ("cp1251", "latin1"):
        try:
            repaired = value.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if _cyrillic_count(repaired) < _cyrillic_count(value):
            return repaired
    return value


SECTION_TITLES = {
    "en": {
        "privacy_intro": "Overview",
        "privacy_collection": "Information we collect",
        "privacy_usage": "How information is used",
        "privacy_rights": "Rights and requests",
        "privacy_contact": "Contact route",
        "cookie_intro": "Cookie framework",
        "cookie_categories": "Technology categories",
        "cookie_management": "Managing preferences",
        "terms_scope": "Service scope",
        "terms_customer": "Customer responsibilities",
        "terms_pricing": "Commercial terms",
        "terms_liability": "Liability",
        "terms_law": "Governing law",
        "notice_identity": "Business identity",
        "notice_market": "Market transparency",
        "notice_contact": "Publication and notice handling",
        "disclaimer_information": "Informational nature",
        "disclaimer_limits": "Operational limits",
        "disclaimer_links": "External references",
    },
    "de": {
        "privacy_intro": "Überblick",
        "privacy_collection": "Welche Informationen wir verarbeiten",
        "privacy_usage": "Wie Informationen verwendet werden",
        "privacy_rights": "Rechte und Anfragen",
        "privacy_contact": "Kontaktweg",
        "cookie_intro": "Cookie-Rahmen",
        "cookie_categories": "Technologiekategorien",
        "cookie_management": "Verwaltung von Präferenzen",
        "terms_scope": "Leistungsumfang",
        "terms_customer": "Pflichten des Kunden",
        "terms_pricing": "Kommerzielle Bedingungen",
        "terms_liability": "Haftung",
        "terms_law": "Anwendbares Recht",
        "notice_identity": "Unternehmensangaben",
        "notice_market": "Markttransparenz",
        "notice_contact": "Veröffentlichung und Zustellung",
        "disclaimer_information": "Informationscharakter",
        "disclaimer_limits": "Operative Grenzen",
        "disclaimer_links": "Externe Verweise",
    },
    "es": {
        "privacy_intro": "Resumen",
        "privacy_collection": "Información que recopilamos",
        "privacy_usage": "Cómo se utiliza la información",
        "privacy_rights": "Derechos y solicitudes",
        "privacy_contact": "Canal de contacto",
        "cookie_intro": "Marco de cookies",
        "cookie_categories": "Categorías de tecnologías",
        "cookie_management": "Gestión de preferencias",
        "terms_scope": "Alcance del servicio",
        "terms_customer": "Responsabilidades del cliente",
        "terms_pricing": "Condiciones comerciales",
        "terms_liability": "Responsabilidad",
        "terms_law": "Ley aplicable",
        "notice_identity": "Identidad empresarial",
        "notice_market": "Transparencia de mercado",
        "notice_contact": "Publicación y notificaciones",
        "disclaimer_information": "Carácter informativo",
        "disclaimer_limits": "Límites operativos",
        "disclaimer_links": "Referencias externas",
    },
    "fr": {
        "privacy_intro": "Vue d'ensemble",
        "privacy_collection": "Informations collectées",
        "privacy_usage": "Utilisation des informations",
        "privacy_rights": "Droits et demandes",
        "privacy_contact": "Canal de contact",
        "cookie_intro": "Cadre cookies",
        "cookie_categories": "Catégories de technologies",
        "cookie_management": "Gestion des préférences",
        "terms_scope": "Périmètre de service",
        "terms_customer": "Responsabilités du client",
        "terms_pricing": "Conditions commerciales",
        "terms_liability": "Responsabilité",
        "terms_law": "Droit applicable",
        "notice_identity": "Identité de l'entreprise",
        "notice_market": "Transparence marché",
        "notice_contact": "Publication et notifications",
        "disclaimer_information": "Nature informative",
        "disclaimer_limits": "Limites opérationnelles",
        "disclaimer_links": "Références externes",
    },
    "it": {
        "privacy_intro": "Panoramica",
        "privacy_collection": "Informazioni raccolte",
        "privacy_usage": "Uso delle informazioni",
        "privacy_rights": "Diritti e richieste",
        "privacy_contact": "Canale di contatto",
        "cookie_intro": "Quadro cookie",
        "cookie_categories": "Categorie di tecnologie",
        "cookie_management": "Gestione delle preferenze",
        "terms_scope": "Perimetro del servizio",
        "terms_customer": "Responsabilità del cliente",
        "terms_pricing": "Condizioni commerciali",
        "terms_liability": "Responsabilità",
        "terms_law": "Legge applicabile",
        "notice_identity": "Identità aziendale",
        "notice_market": "Trasparenza di mercato",
        "notice_contact": "Pubblicazione e notifiche",
        "disclaimer_information": "Natura informativa",
        "disclaimer_limits": "Limiti operativi",
        "disclaimer_links": "Riferimenti esterni",
    },
}


COOKIE_BULLETS = {
    "en": ["Essential cookies", "Preference storage", "Analytics only when lawfully enabled", "Embedded media reviewed before activation"],
    "de": ["Notwendige Cookies", "Präferenzspeicher", "Analyse nur bei zulässiger Aktivierung", "Eingebettete Medien nach Prüfung"],
    "es": ["Cookies esenciales", "Almacenamiento de preferencias", "Analítica solo cuando sea lícita", "Medios embebidos revisados antes de activarse"],
    "fr": ["Cookies essentiels", "Stockage des préférences", "Mesure activée uniquement lorsque la loi le permet", "Médias embarqués vérifiés avant activation"],
    "it": ["Cookie essenziali", "Storage delle preferenze", "Analytics solo quando consentito", "Media incorporati verificati prima dell'attivazione"],
}


NOTICE_TEXT = {
    "en": {
        "privacy": [
            "This policy explains how {entity} handles information connected with {domain} for visitors in {geo_name}.",
            "The publication route, public contact data, and operational notices are aligned with {privacy_reference}. {last_updated_label}: {updated}.",
        ],
        "collection": [
            "We receive information provided through contact requests, onboarding conversations, scheduling enquiries, and follow-up exchanges.",
            "We may also store limited technical request data that is needed to keep the site available, secure, and responsive for the selected market.",
        ],
        "usage": [
            "Information is used to answer enquiries, prepare proposals, coordinate services, maintain records of commercial communication, and support site security.",
            "No hidden profiling or cloaked audience segmentation is used on this site; operational data is reviewed only to improve clarity and service delivery.",
        ],
        "rights": [
            "Visitors may request access, correction, deletion, restriction, objection, or more detail about processing where those rights apply under {privacy_reference}.",
            "Requests can also be escalated to {regulator} when a visitor believes that information has been handled unlawfully.",
        ],
        "contact": [
            "{entity} is the public-facing controller for the processing described here unless a separate written agreement states otherwise.",
            "Privacy requests can be sent to {email}, by phone at {phone}, or by post to {address}.",
        ],
        "cookie": [
            "{domain} uses a consent-aware cookie banner and keeps only the technologies required to render the site, remember preferences, and protect form flows.",
            "Cookie handling is aligned with {cookie_reference} for visitors in {geo_name}.",
        ],
        "cookie_manage": [
            "Visitors can refuse non-essential technologies, clear browser storage, and revisit the cookie notice at any time.",
            "Where consent is required, non-essential technologies must remain inactive until the corresponding choice has been recorded.",
        ],
        "terms": [
            "The site describes a public business profile, sample service structures, and local contact details for {geo_name}.",
            "Pricing, delivery windows, and commercial commitments become binding only when confirmed in a separate written proposal, order, or service agreement.",
        ],
        "customer": [
            "Visitors must provide accurate information, avoid abusive or unlawful submissions, and refrain from interfering with the availability of the site.",
            "Published materials remain subject to intellectual-property rights and may not be reused in a misleading or harmful way.",
        ],
        "pricing": [
            "Commercial terms, taxes, payment windows, and reimbursement rules are defined in the engagement documents applicable to the customer relationship.",
            "Any stated timelines depend on the confirmed scope, local access conditions, and the quality of information supplied during onboarding.",
        ],
        "liability": [
            "The site is provided for informational and contact purposes. Operational details may change as services evolve or local requirements are updated.",
            "To the maximum extent permitted by applicable law, indirect or consequential losses are excluded unless a mandatory rule states otherwise.",
        ],
        "law": [
            "These terms are governed by {jurisdiction}.",
        ],
        "notice_identity": [
            "{entity} publishes this site for the market identified as {geo_name}. Public contact data is kept consistent across the footer, title pattern, and legal documents.",
            "Primary contact route: {email}, {phone}, {address}. Domain in public use: {domain}.",
        ],
        "notice_market": [
            "This page serves as the public legal notice for the selected market and summarises the business identity, notice handling route, and governing regulator.",
            "{eu_notice}",
        ],
        "notice_contact": [
            "Formal notices, privacy requests, and service escalations may be submitted through {email} or by post to {address}.",
            "Regulatory reference for this market: {regulator}.",
        ],
        "disclaimer": [
            "Information published on the site is prepared in good faith to describe a legitimate local business profile, contact route, and example service scope.",
            "Nothing on the site should be treated as legal, financial, or professional advice unless a separate written engagement explicitly says so.",
        ],
        "limits": [
            "Availability, timelines, and examples may change based on the selected market, local operating conditions, and confirmed customer scope.",
            "We review public information regularly, but we do not warrant that every operational detail will remain unchanged at all times.",
        ],
        "links": [
            "If the site links to external services, those services operate under their own terms and privacy rules.",
        ],
    },
    "de": {
        "privacy": [
            "Diese Richtlinie beschreibt, wie {entity} Informationen im Zusammenhang mit {domain} für Besucher in {geo_name} verarbeitet.",
            "Veröffentlichung, öffentliche Kontaktdaten und operative Hinweise orientieren sich an {privacy_reference}. {last_updated_label}: {updated}.",
        ],
        "collection": [
            "Wir erhalten Informationen über Kontaktanfragen, Onboarding-Gespräche, Terminabstimmungen und anschließende Kommunikation.",
            "Zusätzlich können wir begrenzte technische Request-Daten speichern, die für Verfügbarkeit, Sicherheit und Reaktionsfähigkeit der Website erforderlich sind.",
        ],
        "usage": [
            "Informationen werden genutzt, um Anfragen zu beantworten, Angebote zu erstellen, Leistungen zu koordinieren, Kommunikationshistorien zu pflegen und die Site zu schützen.",
            "Verdecktes Profiling oder eine versteckte Zielgruppensteuerung findet nicht statt; operative Daten werden ausschließlich zur Verbesserung von Klarheit und Service genutzt.",
        ],
        "rights": [
            "Soweit Rechte nach {privacy_reference} bestehen, können Besucher Auskunft, Berichtigung, Löschung, Einschränkung, Widerspruch oder weitergehende Informationen verlangen.",
            "Anfragen können auch an {regulator} eskaliert werden, wenn eine unrechtmäßige Verarbeitung vermutet wird.",
        ],
        "contact": [
            "{entity} ist die öffentlich benannte verantwortliche Stelle für die hier beschriebene Verarbeitung, sofern kein gesonderter schriftlicher Vertrag etwas anderes regelt.",
            "Datenschutzanfragen können an {email}, telefonisch an {phone} oder postalisch an {address} gerichtet werden.",
        ],
        "cookie": [
            "{domain} verwendet einen einwilligungsbasierten Cookie-Hinweis und hält nur die Technologien vor, die für Darstellung, Präferenzen und Formularschutz erforderlich sind.",
            "Der Umgang mit Cookies richtet sich für Besucher in {geo_name} nach {cookie_reference}.",
        ],
        "cookie_manage": [
            "Besucher können nicht notwendige Technologien ablehnen, Browser-Speicher löschen und den Cookie-Hinweis jederzeit erneut aufrufen.",
            "Soweit eine Einwilligung erforderlich ist, bleiben nicht notwendige Technologien bis zur dokumentierten Auswahl deaktiviert.",
        ],
        "terms": [
            "Die Website beschreibt ein öffentliches Unternehmensprofil, beispielhafte Leistungsstrukturen und lokale Kontaktdaten für {geo_name}.",
            "Preise, Lieferfenster und verbindliche Zusagen entstehen erst durch ein separates schriftliches Angebot, einen Auftrag oder einen Dienstleistungsvertrag.",
        ],
        "customer": [
            "Besucher müssen zutreffende Angaben machen, missbräuchliche oder rechtswidrige Übermittlungen unterlassen und die Verfügbarkeit der Website nicht beeinträchtigen.",
            "Veröffentlichte Inhalte unterliegen Schutzrechten und dürfen nicht irreführend oder schädlich weiterverwendet werden.",
        ],
        "pricing": [
            "Kommerzielle Bedingungen, Steuern, Zahlungsfristen und Erstattungsregeln ergeben sich aus den jeweils einschlägigen Auftragsunterlagen.",
            "Genannte Zeitfenster hängen vom bestätigten Umfang, lokalen Zugangsbedingungen und der Qualität der im Onboarding bereitgestellten Informationen ab.",
        ],
        "liability": [
            "Die Website dient Informations- und Kontaktzwecken. Operative Details können sich mit Leistungen oder lokalen Anforderungen ändern.",
            "Soweit gesetzlich zulässig, sind mittelbare und Folgeschäden ausgeschlossen, sofern keine zwingende Regel etwas anderes bestimmt.",
        ],
        "law": [
            "Diese Bedingungen unterliegen {jurisdiction}.",
        ],
        "notice_identity": [
            "{entity} veröffentlicht diese Website für den Markt {geo_name}. Öffentliche Kontaktdaten bleiben zwischen Footer, Titelmuster und Rechtstexten konsistent.",
            "Primärer Kontaktweg: {email}, {phone}, {address}. Öffentlich genutzte Domain: {domain}.",
        ],
        "notice_market": [
            "Diese Seite dient als öffentliches Impressum bzw. rechtlicher Hinweis für den gewählten Markt und fasst Identität, Zustellungsweg und zuständige Aufsicht zusammen.",
            "{eu_notice}",
        ],
        "notice_contact": [
            "Formelle Mitteilungen, Datenschutzanfragen und Eskalationen können über {email} oder postalisch an {address} gerichtet werden.",
            "Regulatorische Referenz für diesen Markt: {regulator}.",
        ],
        "disclaimer": [
            "Die auf der Website veröffentlichten Informationen werden nach bestem Wissen erstellt, um ein legitimes lokales Unternehmensprofil, einen Kontaktweg und beispielhafte Leistungen zu beschreiben.",
            "Nichts auf dieser Website stellt ohne gesonderte schriftliche Vereinbarung eine Rechts-, Finanz- oder Fachberatung dar.",
        ],
        "limits": [
            "Verfügbarkeiten, Zeitfenster und Beispiele können sich je nach Markt, lokalen Betriebsbedingungen und bestätigtem Leistungsumfang ändern.",
            "Wir überprüfen öffentliche Informationen regelmäßig, übernehmen jedoch keine Gewähr dafür, dass jeder operative Detailstand jederzeit unverändert bleibt.",
        ],
        "links": [
            "Soweit auf externe Dienste verwiesen wird, gelten dort die jeweiligen eigenen Bedingungen und Datenschutzregeln.",
        ],
    },
    "es": {
        "privacy": [
            "Esta política explica cómo {entity} trata la información vinculada a {domain} para visitantes en {geo_name}.",
            "La publicación, los datos públicos de contacto y los avisos operativos se ajustan a {privacy_reference}. {last_updated_label}: {updated}.",
        ],
        "collection": [
            "Recibimos información mediante solicitudes de contacto, conversaciones de onboarding, consultas operativas y seguimientos posteriores.",
            "También podemos conservar datos técnicos limitados de la solicitud cuando son necesarios para disponibilidad, seguridad y respuesta del sitio.",
        ],
        "usage": [
            "La información se utiliza para responder consultas, preparar propuestas, coordinar servicios, mantener registros comerciales y proteger el sitio.",
            "No se utiliza perfilado oculto ni segmentación encubierta; los datos operativos solo se revisan para mejorar claridad y prestación del servicio.",
        ],
        "rights": [
            "Cuando correspondan derechos bajo {privacy_reference}, los visitantes pueden solicitar acceso, rectificación, supresión, limitación, oposición o más detalle sobre el tratamiento.",
            "Las solicitudes también pueden escalarse ante {regulator} si un visitante considera que la información ha sido tratada de forma ilícita.",
        ],
        "contact": [
            "{entity} actúa como responsable visible del tratamiento descrito aquí, salvo que un acuerdo escrito específico disponga lo contrario.",
            "Las solicitudes de privacidad pueden enviarse a {email}, por teléfono al {phone} o por correo postal a {address}.",
        ],
        "cookie": [
            "{domain} utiliza un aviso de cookies con control de consentimiento y mantiene solo las tecnologías necesarias para mostrar el sitio, recordar preferencias y proteger formularios.",
            "La gestión de cookies para visitantes en {geo_name} se alinea con {cookie_reference}.",
        ],
        "cookie_manage": [
            "Los visitantes pueden rechazar tecnologías no esenciales, borrar el almacenamiento del navegador y revisar de nuevo el aviso de cookies en cualquier momento.",
            "Cuando el consentimiento sea obligatorio, las tecnologías no esenciales deben permanecer inactivas hasta que se registre la elección correspondiente.",
        ],
        "terms": [
            "El sitio describe un perfil empresarial público, ejemplos de servicios y datos de contacto locales para {geo_name}.",
            "Los precios, plazos y compromisos comerciales solo serán vinculantes cuando se confirmen en una propuesta, pedido o contrato separado por escrito.",
        ],
        "customer": [
            "Los visitantes deben facilitar información exacta, abstenerse de envíos abusivos o ilícitos y no interferir con la disponibilidad del sitio.",
            "Los materiales publicados siguen sujetos a derechos de propiedad intelectual y no pueden reutilizarse de forma engañosa o dañina.",
        ],
        "pricing": [
            "Las condiciones comerciales, impuestos, pagos y reembolsos se definen en la documentación aplicable a cada relación con el cliente.",
            "Los plazos indicados dependen del alcance confirmado, de las condiciones de acceso locales y de la calidad de la información aportada en onboarding.",
        ],
        "liability": [
            "El sitio se ofrece con fines informativos y de contacto. Los detalles operativos pueden variar a medida que cambian los servicios o los requisitos locales.",
            "En la máxima medida permitida por la ley aplicable, quedan excluidas las pérdidas indirectas o consecuenciales salvo norma imperativa en sentido contrario.",
        ],
        "law": [
            "Estos términos se rigen por {jurisdiction}.",
        ],
        "notice_identity": [
            "{entity} publica este sitio para el mercado identificado como {geo_name}. Los datos públicos de contacto se mantienen coherentes entre footer, patrón de título y documentos legales.",
            "Canal principal de contacto: {email}, {phone}, {address}. Dominio público utilizado: {domain}.",
        ],
        "notice_market": [
            "Esta página sirve como aviso legal público para el mercado seleccionado y resume la identidad empresarial, la vía de notificaciones y el regulador competente.",
            "{eu_notice}",
        ],
        "notice_contact": [
            "Las notificaciones formales, solicitudes de privacidad y escalaciones de servicio pueden remitirse a {email} o por correo postal a {address}.",
            "Referencia regulatoria para este mercado: {regulator}.",
        ],
        "disclaimer": [
            "La información publicada en el sitio se prepara de buena fe para describir un perfil comercial legítimo, un canal de contacto y un alcance de servicio de ejemplo.",
            "Nada en el sitio debe interpretarse como asesoramiento legal, financiero o profesional salvo acuerdo escrito independiente.",
        ],
        "limits": [
            "Disponibilidad, plazos y ejemplos pueden cambiar según el mercado seleccionado, las condiciones operativas locales y el alcance confirmado del cliente.",
            "Revisamos la información pública con regularidad, pero no garantizamos que cada detalle operativo permanezca inalterado en todo momento.",
        ],
        "links": [
            "Si el sitio enlaza a servicios externos, dichos servicios operan bajo sus propias condiciones y políticas de privacidad.",
        ],
    },
    "fr": {
        "privacy": [
            "Cette politique explique comment {entity} traite les informations liées à {domain} pour les visiteurs situés en {geo_name}.",
            "La publication, les coordonnées publiques et les avis opérationnels sont alignés sur {privacy_reference}. {last_updated_label} : {updated}.",
        ],
        "collection": [
            "Nous recevons des informations via les demandes de contact, échanges d'onboarding, questions opérationnelles et suivis ultérieurs.",
            "Nous pouvons également conserver des données techniques limitées lorsque cela est nécessaire à la disponibilité, la sécurité et la réactivité du site.",
        ],
        "usage": [
            "Les informations sont utilisées pour répondre aux demandes, préparer des propositions, coordonner les prestations, conserver l'historique commercial et protéger le site.",
            "Aucun profilage caché ni segmentation dissimulée n'est utilisé ; les données opérationnelles servent uniquement à améliorer la clarté et la qualité de service.",
        ],
        "rights": [
            "Lorsque des droits existent au titre de {privacy_reference}, les visiteurs peuvent demander l'accès, la rectification, l'effacement, la limitation, l'opposition ou davantage d'informations.",
            "Les demandes peuvent aussi être portées auprès de {regulator} si un visiteur estime que ses informations ont été traitées illicitement.",
        ],
        "contact": [
            "{entity} agit comme responsable public du traitement décrit ici, sauf disposition contraire d'un accord écrit distinct.",
            "Les demandes relatives à la confidentialité peuvent être adressées à {email}, par téléphone au {phone} ou par courrier à {address}.",
        ],
        "cookie": [
            "{domain} utilise une bannière cookies tenant compte du consentement et ne conserve que les technologies nécessaires à l'affichage du site, à la mémorisation des préférences et à la protection des formulaires.",
            "La gestion des cookies pour les visiteurs en {geo_name} s'aligne sur {cookie_reference}.",
        ],
        "cookie_manage": [
            "Les visiteurs peuvent refuser les technologies non essentielles, effacer le stockage navigateur et rouvrir l'avis cookies à tout moment.",
            "Lorsque le consentement est requis, les technologies non essentielles doivent rester inactives jusqu'à l'enregistrement du choix correspondant.",
        ],
        "terms": [
            "Le site décrit un profil d'entreprise public, des structures de services d'exemple et des coordonnées locales pour {geo_name}.",
            "Les tarifs, délais et engagements commerciaux ne deviennent obligatoires qu'après confirmation dans une proposition, commande ou convention écrite distincte.",
        ],
        "customer": [
            "Les visiteurs doivent fournir des informations exactes, éviter tout envoi abusif ou illicite et ne pas perturber la disponibilité du site.",
            "Les contenus publiés demeurent protégés par les droits de propriété intellectuelle et ne peuvent être réutilisés de manière trompeuse ou nuisible.",
        ],
        "pricing": [
            "Les conditions commerciales, taxes, échéances de paiement et remboursements sont définis dans la documentation applicable à chaque relation client.",
            "Les délais annoncés dépendent du périmètre confirmé, des conditions d'accès locales et de la qualité des informations fournies lors de l'onboarding.",
        ],
        "liability": [
            "Le site est fourni à des fins d'information et de contact. Les détails opérationnels peuvent évoluer avec les services ou les exigences locales.",
            "Dans toute la mesure permise par la loi applicable, les pertes indirectes ou consécutives sont exclues sauf règle impérative contraire.",
        ],
        "law": [
            "Ces conditions sont régies par {jurisdiction}.",
        ],
        "notice_identity": [
            "{entity} publie ce site pour le marché identifié comme {geo_name}. Les coordonnées publiques restent cohérentes entre footer, modèle de titre et documents légaux.",
            "Canal principal de contact : {email}, {phone}, {address}. Domaine public utilisé : {domain}.",
        ],
        "notice_market": [
            "Cette page sert de notice légale publique pour le marché sélectionné et résume l'identité de l'entreprise, la voie de notification et l'autorité compétente.",
            "{eu_notice}",
        ],
        "notice_contact": [
            "Les notifications formelles, demandes relatives aux données et escalades de service peuvent être adressées à {email} ou par courrier à {address}.",
            "Référence réglementaire pour ce marché : {regulator}.",
        ],
        "disclaimer": [
            "Les informations publiées sur le site sont préparées de bonne foi afin de présenter un profil d'activité légitime, un canal de contact et un périmètre de service d'exemple.",
            "Aucune information du site ne doit être interprétée comme un conseil juridique, financier ou professionnel en l'absence d'un accord écrit distinct.",
        ],
        "limits": [
            "Les disponibilités, délais et exemples peuvent évoluer selon le marché choisi, les conditions opérationnelles locales et le périmètre confirmé du client.",
            "Nous révisons régulièrement les informations publiques sans garantir que chaque détail opérationnel restera inchangé à tout moment.",
        ],
        "links": [
            "Si le site renvoie vers des services externes, ceux-ci fonctionnent selon leurs propres conditions et règles de confidentialité.",
        ],
    },
    "it": {
        "privacy": [
            "Questa informativa spiega come {entity} tratta le informazioni collegate a {domain} per i visitatori in {geo_name}.",
            "Pubblicazione, contatti pubblici e avvisi operativi sono allineati a {privacy_reference}. {last_updated_label}: {updated}.",
        ],
        "collection": [
            "Riceviamo informazioni tramite richieste di contatto, conversazioni di onboarding, domande operative e successivi follow-up.",
            "Possiamo inoltre conservare dati tecnici limitati quando sono necessari per disponibilità, sicurezza e reattività del sito.",
        ],
        "usage": [
            "Le informazioni sono utilizzate per rispondere alle richieste, preparare proposte, coordinare i servizi, mantenere tracciabilità commerciale e proteggere il sito.",
            "Non viene utilizzata profilazione nascosta né segmentazione occulta; i dati operativi servono solo a migliorare chiarezza e qualità del servizio.",
        ],
        "rights": [
            "Quando previsti da {privacy_reference}, i visitatori possono richiedere accesso, rettifica, cancellazione, limitazione, opposizione o maggiori dettagli sul trattamento.",
            "Le richieste possono anche essere portate all'attenzione di {regulator} se il visitatore ritiene che le informazioni siano state trattate illecitamente.",
        ],
        "contact": [
            "{entity} agisce come titolare pubblico del trattamento qui descritto, salvo diversa previsione in un accordo scritto separato.",
            "Le richieste privacy possono essere inviate a {email}, per telefono al {phone} o per posta a {address}.",
        ],
        "cookie": [
            "{domain} utilizza un banner cookie orientato al consenso e mantiene solo le tecnologie necessarie a rendere il sito visibile, ricordare preferenze e proteggere i form.",
            "La gestione dei cookie per i visitatori in {geo_name} è allineata a {cookie_reference}.",
        ],
        "cookie_manage": [
            "I visitatori possono rifiutare tecnologie non essenziali, cancellare lo storage del browser e riaprire l'avviso cookie in qualsiasi momento.",
            "Quando il consenso è richiesto, le tecnologie non essenziali devono restare inattive fino alla registrazione della scelta.",
        ],
        "terms": [
            "Il sito descrive un profilo aziendale pubblico, strutture di servizio esemplificative e contatti locali per {geo_name}.",
            "Prezzi, tempistiche e impegni commerciali diventano vincolanti solo dopo conferma in una proposta, ordine o accordo scritto separato.",
        ],
        "customer": [
            "I visitatori devono fornire informazioni corrette, evitare invii abusivi o illeciti e non interferire con la disponibilità del sito.",
            "I contenuti pubblicati restano soggetti a diritti di proprietà intellettuale e non possono essere riutilizzati in modo ingannevole o dannoso.",
        ],
        "pricing": [
            "Condizioni commerciali, imposte, finestre di pagamento e rimborsi sono definite nella documentazione applicabile al singolo rapporto con il cliente.",
            "Le tempistiche indicate dipendono dal perimetro confermato, dalle condizioni di accesso locali e dalla qualità delle informazioni fornite in onboarding.",
        ],
        "liability": [
            "Il sito è fornito per finalità informative e di contatto. I dettagli operativi possono cambiare con i servizi o con requisiti locali aggiornati.",
            "Nella massima misura consentita dalla legge applicabile, restano escluse le perdite indirette o consequenziali salvo diversa norma imperativa.",
        ],
        "law": [
            "Questi termini sono disciplinati da {jurisdiction}.",
        ],
        "notice_identity": [
            "{entity} pubblica questo sito per il mercato identificato come {geo_name}. I contatti pubblici restano coerenti tra footer, pattern del titolo e documenti legali.",
            "Canale principale di contatto: {email}, {phone}, {address}. Dominio pubblico utilizzato: {domain}.",
        ],
        "notice_market": [
            "Questa pagina funziona come avviso legale pubblico per il mercato selezionato e riassume identità aziendale, canale di notifica e regolatore competente.",
            "{eu_notice}",
        ],
        "notice_contact": [
            "Notifiche formali, richieste privacy ed escalation di servizio possono essere inviate a {email} o per posta a {address}.",
            "Riferimento regolatorio per questo mercato: {regulator}.",
        ],
        "disclaimer": [
            "Le informazioni pubblicate sul sito sono predisposte in buona fede per descrivere un profilo aziendale legittimo, un canale di contatto e un perimetro di servizio esemplificativo.",
            "Nulla di quanto pubblicato deve essere interpretato come consulenza legale, finanziaria o professionale in assenza di un accordo scritto separato.",
        ],
        "limits": [
            "Disponibilità, tempistiche ed esempi possono cambiare in base al mercato selezionato, alle condizioni operative locali e al perimetro confermato del cliente.",
            "Rivediamo regolarmente le informazioni pubbliche senza garantire che ogni dettaglio operativo resti invariato in ogni momento.",
        ],
        "links": [
            "Se il sito rimanda a servizi esterni, tali servizi operano secondo proprie condizioni e regole privacy.",
        ],
    },
}


def _titles(language: str) -> dict[str, str]:
    legal = LOCALE_PACKS[language]["legal"]
    return {
        "privacy-policy.php": _clean_text(legal["privacy_title"]),
        "cookie-policy.php": _clean_text(legal["cookie_title"]),
        "terms-of-service.php": _clean_text(legal["terms_title"]),
        "legal-notice.php": _clean_text(legal["legal_notice_title"]),
        "disclaimer.php": _clean_text(legal["disclaimer_title"]),
    }


def _section(title: str, paragraphs: list[str], bullets: list[str] | None = None) -> str:
    body = "".join(f"<p>{escape(_clean_text(paragraph))}</p>" for paragraph in paragraphs)
    bullet_html = ""
    if bullets:
        bullet_html = "<ul>" + "".join(f"<li>{escape(_clean_text(item))}</li>" for item in bullets) + "</ul>"
    return f"<section><h2>{escape(_clean_text(title))}</h2>{body}{bullet_html}</section>"


def _eu_notice(language: str, geo: str) -> str:
    if geo not in EU_GEOS:
        messages = {
            "en": "For this market, the notice focuses on public business identity, lawful contact handling, and regulatory transparency.",
            "de": "Für diesen Markt konzentriert sich der Hinweis auf öffentliche Unternehmensangaben, rechtmäßige Kontaktbearbeitung und regulatorische Transparenz.",
            "es": "Para este mercado, el aviso se centra en identidad pública, gestión lícita del contacto y transparencia regulatoria.",
            "fr": "Pour ce marché, l'avis se concentre sur l'identité publique, le traitement licite des contacts et la transparence réglementaire.",
            "it": "Per questo mercato, l'avviso si concentra su identità pubblica, gestione lecita dei contatti e trasparenza regolatoria.",
        }
        return _clean_text(messages[language])
    messages = {
        "en": "For EU-facing markets this page also serves as the market-specific legal notice or imprint, summarising transparency obligations for publication, cookies, and data handling.",
        "de": "Für EU-bezogene Märkte dient diese Seite zugleich als marktspezifisches Impressum und fasst Transparenzpflichten zu Veröffentlichung, Cookies und Datenverarbeitung zusammen.",
        "es": "Para mercados con alcance UE, esta página también actúa como aviso legal o imprint específico del mercado y resume obligaciones de transparencia sobre publicación, cookies y datos.",
        "fr": "Pour les marchés orientés UE, cette page sert aussi de notice légale ou imprint spécifique et résume les obligations de transparence relatives à la publication, aux cookies et aux données.",
        "it": "Per i mercati UE, questa pagina svolge anche la funzione di avviso legale o imprint specifico e riassume gli obblighi di trasparenza su pubblicazione, cookie e dati.",
    }
    return _clean_text(messages[language])


def _registry() -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for language in LOCALE_PACKS:
        for geo, geo_pack in GEO_PACKS.items():
            key = f"{language}-{geo}"
            registry[key] = {
                "key": key,
                "language": language,
                "geo": geo,
                "geo_name": LOCALE_PACKS[language]["geo_names"][geo],
                "jurisdiction": geo_pack["legal"]["jurisdiction"],
                "governing_law": geo_pack["legal"]["jurisdiction"],
                "privacy_reference": geo_pack["legal"]["privacy_reference"],
                "cookie_reference": geo_pack["legal"]["cookie_reference"],
                "regulator": geo_pack["legal"]["regulator"],
                "titles": _titles(language),
                "required_docs": LEGAL_DOC_FILES,
            }
    return registry


LEGAL_PACK_REGISTRY = _registry()


def resolve_legal_pack(language: str, geo: str, company: CompanyProfile, updated: str, last_updated_label: str) -> LegalPack:
    key = f"{language}-{geo}"
    if key not in LEGAL_PACK_REGISTRY:
        raise ValueError(f"Legal pack is missing for {key}.")
    entry = LEGAL_PACK_REGISTRY[key]
    templates = NOTICE_TEXT[language]
    sections = SECTION_TITLES[language]
    context = {
        "entity": company.legal_entity_name,
        "domain": company.domain,
        "geo_name": entry["geo_name"],
        "privacy_reference": entry["privacy_reference"],
        "cookie_reference": entry["cookie_reference"],
        "email": str(company.email),
        "phone": company.phone,
        "address": company.address,
        "jurisdiction": entry["jurisdiction"],
        "regulator": entry["regulator"],
        "updated": updated,
        "last_updated_label": last_updated_label,
        "eu_notice": _eu_notice(language, geo),
    }

    def render(name: str) -> list[str]:
        return [_clean_text(item.format(**context)) for item in templates[name]]

    privacy_html = "".join(
        [
            _section(sections["privacy_intro"], render("privacy")),
            _section(sections["privacy_collection"], render("collection")),
            _section(sections["privacy_usage"], render("usage")),
            _section(sections["privacy_rights"], render("rights")),
            _section(sections["privacy_contact"], render("contact")),
        ]
    )
    cookie_html = "".join(
        [
            _section(sections["cookie_intro"], render("cookie")),
            _section(sections["cookie_categories"], [], [_clean_text(item) for item in COOKIE_BULLETS[language]]),
            _section(sections["cookie_management"], render("cookie_manage")),
            _section(sections["privacy_contact"], render("contact")),
        ]
    )
    terms_html = "".join(
        [
            _section(sections["terms_scope"], render("terms")),
            _section(sections["terms_customer"], render("customer")),
            _section(sections["terms_pricing"], render("pricing")),
            _section(sections["terms_liability"], render("liability")),
            _section(sections["terms_law"], render("law")),
        ]
    )
    legal_notice_html = "".join(
        [
            _section(sections["notice_identity"], render("notice_identity")),
            _section(sections["notice_market"], render("notice_market")),
            _section(sections["notice_contact"], render("notice_contact")),
        ]
    )
    disclaimer_html = "".join(
        [
            _section(sections["disclaimer_information"], render("disclaimer")),
            _section(sections["disclaimer_limits"], render("limits")),
            _section(sections["disclaimer_links"], render("links")),
        ]
    )
    return LegalPack(
        key=key,
        jurisdiction=entry["jurisdiction"],
        governing_law=entry["governing_law"],
        regulator=entry["regulator"],
        required_docs=list(entry["required_docs"]),
        document_titles=dict(entry["titles"]),
        privacy_html=privacy_html,
        cookie_html=cookie_html,
        terms_html=terms_html,
        legal_notice_html=legal_notice_html,
        disclaimer_html=disclaimer_html,
    )
