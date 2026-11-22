"""Genera due PDF di esempio (contenuto fittizio) per provare l'assistente."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

OUT = Path("data/pdfs")

DISCLAIMER = (
    "Documento di esempio a contenuto fittizio, creato per un progetto dimostrativo. "
    "Non rappresenta le procedure di alcuna compagnia aerea reale."
)

# Ogni sezione: (titolo, [paragrafi], nuova_pagina_prima)
PROCEDURE = (
    "Procedura operativa: gestione dei ritardi alla partenza",
    [
        (
            "1. Scopo e ambito",
            [
                "Questa procedura descrive come il personale di cabina e il personale operativo gestiscono un ritardo alla partenza di un volo passeggeri. Si applica a tutti i voli in partenza dalla base operativa.",
                "Un ritardo alla partenza è la differenza, in minuti, tra l'orario di partenza programmato e l'orario effettivo in cui l'aeromobile lascia la piazzola (off-block).",
            ],
            False,
        ),
        (
            "2. Classificazione dei ritardi",
            [
                "I ritardi sono classificati in tre livelli. Ritardo lieve: fino a 30 minuti. Ritardo moderato: da 31 a 120 minuti. Ritardo grave: oltre 120 minuti.",
                "La classificazione si basa sul ritardo previsto comunicato dal responsabile operativo di scalo e viene aggiornata se la previsione cambia.",
            ],
            False,
        ),
        (
            "3. Ritardo lieve (fino a 30 minuti)",
            [
                "Il capo cabina informa l'equipaggio e, entro 10 minuti dall'orario di partenza programmato, effettua un annuncio ai passeggeri indicando la nuova ora prevista di partenza.",
                "Non sono richieste azioni di assistenza. Il ritardo viene comunque registrato nel rapporto di volo.",
            ],
            False,
        ),
        (
            "4. Ritardo moderato (da 31 a 120 minuti)",
            [
                "Il capo cabina effettua un annuncio iniziale e poi un aggiornamento ogni 30 minuti, anche quando non ci sono novità.",
                "Viene distribuita acqua a tutti i passeggeri a bordo. Il capo cabina chiede al responsabile operativo di scalo l'elenco dei passeggeri con coincidenze a rischio e lo comunica al personale di terra.",
                "Il responsabile operativo di scalo va informato entro 15 minuti dal passaggio al livello moderato.",
            ],
            False,
        ),
        (
            "5. Ritardo grave (oltre 120 minuti)",
            [
                "Oltre alle azioni previste per il ritardo moderato, il capo cabina organizza la distribuzione di bevande e snack. Se il ritardo supera i 180 minuti, viene offerto un pasto.",
                "Lo sbarco dei passeggeri è deciso congiuntamente dal comandante e dal responsabile operativo di scalo. Il capo cabina non può autorizzare lo sbarco da solo.",
                "In caso di sbarco, il capo cabina verifica che a bordo non restino bagagli o oggetti non reclamati e comunica al personale di terra il numero di passeggeri sbarcati.",
            ],
            True,
        ),
        (
            "6. Registrazione del ritardo",
            [
                "Ogni ritardo deve essere registrato con i minuti effettivi e con un motivo. I motivi ammessi sono: tecnico, meteo, traffico aereo, operativo, passeggeri, altro.",
                "Il ritardo in partenza e il ritardo in arrivo sono registrati separatamente. Il motivo è obbligatorio per tutti i ritardi superiori a 15 minuti.",
                "Il rapporto di volo va completato entro la fine del servizio e consegnato al responsabile operativo.",
            ],
            False,
        ),
        (
            "7. Ruoli e responsabilità",
            [
                "Capo cabina: annunci ai passeggeri, assistenza a bordo, registrazione nel rapporto di volo. Responsabile operativo di scalo: previsione del ritardo, gestione delle coincidenze, decisione sullo sbarco insieme al comandante. Comandante: decisioni di sicurezza e sbarco.",
            ],
            False,
        ),
    ],
)

FAQ = (
    "Domande frequenti per il personale operativo",
    [
        (
            "Dopo quanto tempo un ritardo è considerato grave?",
            ["Un ritardo è considerato grave quando supera i 120 minuti. Tra 31 e 120 minuti è moderato, fino a 30 minuti è lieve."],
            False,
        ),
        (
            "Con quale frequenza vanno fatti gli annunci durante un ritardo moderato?",
            ["Un annuncio iniziale e poi un aggiornamento ogni 30 minuti, anche senza novità."],
            False,
        ),
        (
            "Chi può autorizzare lo sbarco dei passeggeri?",
            ["Lo sbarco è deciso dal comandante insieme al responsabile operativo di scalo. Il capo cabina da solo non può autorizzarlo."],
            False,
        ),
        (
            "Quando viene offerto un pasto ai passeggeri?",
            ["Un pasto viene offerto quando il ritardo supera i 180 minuti. Prima di quella soglia sono previsti acqua, bevande e snack in base al livello del ritardo."],
            False,
        ),
        (
            "Il motivo del ritardo è sempre obbligatorio?",
            ["No. Il motivo è obbligatorio solo per i ritardi superiori a 15 minuti. I motivi ammessi sono tecnico, meteo, traffico aereo, operativo, passeggeri, altro."],
            True,
        ),
        (
            "Cosa fare se un passeggero rischia di perdere una coincidenza?",
            ["Il capo cabina chiede al responsabile operativo di scalo l'elenco dei passeggeri con coincidenze a rischio e lo comunica al personale di terra, in modo che possano preparare la riprenotazione."],
            False,
        ),
        (
            "Entro quando va consegnato il rapporto di volo?",
            ["Entro la fine del servizio, al responsabile operativo."],
            False,
        ),
        (
            "Cosa succede in caso di ritardo dovuto al maltempo?",
            ["La procedura è la stessa, ma il motivo da registrare è meteo. Se le condizioni riguardano la sicurezza, ogni decisione spetta al comandante."],
            False,
        ),
    ],
)


def build_pdf(path: Path, title: str, sections: list) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, title=title, author="Documento di esempio")
    story = [Paragraph(title, styles["Title"]), Paragraph(DISCLAIMER, styles["Italic"]), Spacer(1, 16)]
    for heading, paragraphs, new_page in sections:
        if new_page:
            story.append(PageBreak())
        story.append(Paragraph(heading, styles["Heading2"]))
        for text in paragraphs:
            story.append(Paragraph(text, styles["BodyText"]))
        story.append(Spacer(1, 8))
    doc.build(story)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    build_pdf(OUT / "procedura_ritardi_partenza.pdf", *PROCEDURE)
    build_pdf(OUT / "faq_operazioni.pdf", *FAQ)
    print(f"PDF creati in {OUT}/")
