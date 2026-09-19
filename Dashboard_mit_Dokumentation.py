#!/usr/bin/env python
# coding: utf-8

# In[4]:


import os
import json
from enum import Enum
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align
from rich.box import SQUARE, DOUBLE

#=====================
#    Datenstruktur
#=====================

class KursStatus(Enum):
    """Status des Kurses."""
    OFFEN = "Offen"
    BESTANDEN = "Bestanden"

class Pruefungsleistung:
    """Repräsentiert die erbrachte Prüfungsleistung"""
    def __init__(self, note: float):
        self.note = note

class Kurs:
    """Repräsentiert einen Kurs innerhalb des Studiengangs."""
    def __init__(self, kurstitel: str, ects_punkte: int, status: KursStatus = KursStatus.OFFEN):
        self.kurstitel = kurstitel
        self.ects_punkte = ects_punkte
        self.status = status
        self.pruefungsleistung = None

#==============================
#      Logik und Berechnung
#==============================

class Studiengang:
    """Verwaltet alle Kurse und berechnet den aktuellen Fortschritt."""
    def __init__(self, name: str, angestrebte_note: float, gesamt_ects: int):
        self.name = name
        self.angestrebte_note = angestrebte_note
        self.gesamt_ects = gesamt_ects
        self.kurse = []

    @property
    def aktuelle_durchschnittsnote(self) -> float:
        """Berechnet den Notendurchschnitt aller bestandenen Kurse."""
        b = [k for k in self.kurse if k.status == KursStatus.BESTANDEN and k.pruefungsleistung]
        if not b: return 0.0
        return round(sum(k.pruefungsleistung.note for k in b) / len(b), 2)

    @property
    def erreichte_ects(self) -> int:
        """Summiert die ECTS-Punkte aller bestandener Kurse"""
        return sum(k.ects_punkte for k in self.kurse if k.status == KursStatus.BESTANDEN)

    def kursHinzufuegen(self, kurs: Kurs) -> None:
        """Fügt dem Studiengang einen neuen Kurs hinzu."""
        self.kurse.append(kurs)

    def kursBestehen(self, kurs: Kurs, note: float) -> bool:
        """Markiert einen offenen Kurs als bestanden und trägt die Note ein."""
        if kurs in self.kurse and kurs.status == KursStatus.OFFEN:
            kurs.pruefungsleistung = Pruefungsleistung(note)
            kurs.status = KursStatus.BESTANDEN
            return True
        return False

    def kursLoeschen(self, kurs: Kurs) -> None:
        """Entfernt einen Kurs permanent."""
        if kurs in self.kurse:
            self.kurse.remove(kurs)

#===============================
#    Speicherung und Zugriff
#===============================

class DataManager:
    """Verantwortlich für das Laden und Speichern der Daten."""
    def __init__(self, dateipfad: str):
        self.dateipfad = dateipfad

    def daten_speichern(self, studiengang: Studiengang) -> bool:
        """Speichert den aktuellen Zustand des Studiengangs."""
        liste_kurse = []
        for k in studiengang.kurse:
            liste_kurse.append({
                "kurstitel": k.kurstitel,
                "ects_punkte": k.ects_punkte,
                "status": k.status.value,
                "note": k.pruefungsleistung.note if k.pruefungsleistung else None
            })
        daten = {
            "name": studiengang.name,
            "angestrebte_note": studiengang.angestrebte_note,
            "gesamt_ects": studiengang.gesamt_ects,
            "kurse": liste_kurse
        }
        with open(self.dateipfad, "w", encoding="utf-8") as f:
            json.dump(daten, f, indent=4, ensure_ascii=False)
        return True

    def daten_laden(self) -> Studiengang:
        """Lädt die gespeicherten Daten."""
        if not os.path.exists(self.dateipfad):
            return Studiengang("CYBER SECURITY", 1.5, 180) #Hier kann der Name des Studiengangs, die angestrebte Note und die gesamt ECTS geändert werden.
        with open(self.dateipfad, "r", encoding="utf-8") as f:
            daten = json.load(f)
        studiengang = Studiengang(daten.get("name", "CYBER SECURITY"), daten.get("angestrebte_note", 1.5), daten.get("gesamt_ects", 180))
        for k_data in daten.get("kurse", []):
            st = KursStatus.BESTANDEN if k_data["status"] == "Bestanden" else KursStatus.OFFEN
            k = Kurs(k_data["kurstitel"], k_data["ects_punkte"], st)
            if k_data["note"] is not None:
                k.pruefungsleistung = Pruefungsleistung(k_data["note"])
            studiengang.kurse.append(k)
        return studiengang

#==========================
#    UI und Interaktion
#==========================

class DashboardUI:
    """Terminal-Oberfläche zur Darstellung und Steuerung."""
    def __init__(self, manager: DataManager, studiengang: Studiengang):
        self._manager = manager
        self._studiengang = studiengang
        self.console = Console()

    def start(self) -> None:
        """Startet die Endlosschleife der Benutzeroberfläche."""
        while True:
            try:
                self.zeige_hauptmenue()
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[yellow]Programm beendet.[/yellow]")
                break

    def zeige_hauptmenue(self) -> None:
        """Erzeugt die Tabellen, ECTS-Übersicht und wertet die Menüauswahl aus."""
        self.console.clear()
        self.console.print(Panel(Align.center(f"[bold white]{self._studiengang.name}[/bold white]"), box=DOUBLE, expand=True))

        offene = [k for k in self._studiengang.kurse if k.status == KursStatus.OFFEN]
        bestandene = [k for k in self._studiengang.kurse if k.status == KursStatus.BESTANDEN]

        #Tabelle der offenen Kurse
        self.console.print(Align.center("[italic white]Offene Kurse[/italic white]"))
        t_offen = Table(box=SQUARE, expand=True, header_style="bold white")
        t_offen.add_column("ID", justify="center", width=10)
        t_offen.add_column("Kursname", justify="left")
        t_offen.add_column("ECTS", justify="right", width=15)

        if not offene:
            t_offen.add_row("-", "[dim]Keine offenen Kurse eingetragen[/dim]", "-")
        else:
            for idx, k in enumerate(offene, start=1):
                t_offen.add_row(str(idx), k.kurstitel, str(k.ects_punkte))
        self.console.print(t_offen)

        #Tabelle der bestandenen Kurse
        self.console.print(Align.center("[italic white]Bestandene Kurse[/italic white]"))
        t_best = Table(box=SQUARE, expand=True, header_style="bold green")
        t_best.add_column("Kursname", justify="left")
        t_best.add_column("ECTS", justify="right", width=15)
        t_best.add_column("Note", justify="right", width=15)

        if not bestandene:
            t_best.add_row("[dim]Keine bestandenen Kurse vorhanden[/dim]", "-", "-")
        else:
            for k in bestandene:
                n_str = f"{k.pruefungsleistung.note:.1f}" if k.pruefungsleistung else "-"
                t_best.add_row(k.kurstitel, str(k.ects_punkte), n_str)
        self.console.print(t_best)

        #Status-Boxen
        p_ects = Panel(f"Erreicht: [bold white]{self._studiengang.erreichte_ects}[/bold white] / Gesamt: {self._studiengang.gesamt_ects}", title="Übersicht ECTS", title_align="left", border_style="blue", expand=True)
        p_note = Panel(f"Aktuell: [bold white]{self._studiengang.aktuelle_durchschnittsnote:.2f}[/bold white] / Ziel: {self._studiengang.angestrebte_note:.1f}", title="Durchschnittsnote", title_align="left", border_style="magenta", expand=True)
        self.console.print(Columns([p_ects, p_note], expand=True))

        self.console.print("\n[bold white]Optionen:[/bold white]")
        self.console.print(" [1] Neuen offenen Kurs hinzufügen | [2] Kurs bestehen | [3] Kurs löschen | [4] Beenden")

        #Interaktives Menü
        wahl = self.console.input("Wähle eine Aktion [1/2/3/4] (1): ").strip()
        if wahl == "" or wahl == "1":
            self.maske_kurs_hinzufuegen()
        elif wahl == "2":
            self.maske_kurs_bestehen(offene)
        elif wahl == "3":
            self.maske_kurs_loeschen()
        elif wahl == "4":
            exit(0)

    def maske_kurs_hinzufuegen(self) -> None:
        """Eingabemaske für das Hinzufügen eines neuen Kurses."""
        self.console.print("\n[bold blue]--- Neuen Kurs anlegen ---[/bold blue]")
        name = self.console.input("Kursname: ").strip()
        if not name: return
        ects_in = self.console.input("ECTS-Punkte: ").strip()
        if not ects_in.isdigit(): return
        self._studiengang.kursHinzufuegen(Kurs(name, int(ects_in)))
        self._manager.daten_speichern(self._studiengang)

    def maske_kurs_bestehen(self, offene: List[Kurs]) -> None:
        """Eingabemaske für das HInzufügen einer Note."""
        if not offene: return
        self.console.print("\n[bold green]--- Kurs als bestanden markieren ---[/bold green]")
        idx_in = self.console.input("Gib die ID des Kurses ein: ").strip()
        if not idx_in.isdigit(): return
        idx = int(idx_in) - 1
        if idx < 0 or idx >= len(offene): return
        note_in = self.console.input(f"Note für '{offene[idx].kurstitel}': ").strip()
        try:
            note = float(note_in)
            if 1.0 <= note <= 4.0:
                self._studiengang.kursBestehen(offene[idx], note)
                self._manager.daten_speichern(self._studiengang)
        except:
            pass

    def maske_kurs_loeschen(self) -> None:
        """Eingabemaske um einen Kurs dauerhaft zu löschen."""
        if not self._studiengang.kurse:
            self.console.print("[red]\nKeine Kurse zum Löschen vorhanden![/red]")
            self.console.input("\nDrücke Enter...")
            return
        self.console.print("\n[bold red]--- Kurs löschen ---[/bold red]")
        for i, k in enumerate(self._studiengang.kurse, start=1):
            self.console.print(f" [{i}] {k.kurstitel} ({k.status.value})")
        idx_in = self.console.input("\nGib die Nummer des zu löschenden Kurses ein: ").strip()
        if not idx_in.isdigit(): return
        idx = int(idx_in) - 1
        if idx < 0 or idx >= len(self._studiengang.kurse): return
        self._studiengang.kursLoeschen(self._studiengang.kurse[idx])
        self._manager.daten_speichern(self._studiengang)
        self.console.print("[green]Kurs erfolgreich gelöscht![/green]")

#=======================
#    Anwendungsstart
#=======================
class Application:
    """Initialisiert die Kernkomponenten und startet das Programm."""
    def run(self) -> None:
        manager = DataManager("daten.json") #Datenschicht initialisieren
        studiengang = manager.daten_laden() #Bestehende Daten laden
        ui = DashboardUI(manager, studiengang) #UI erzeugen und mit der Logik sowie Datenschicht verbinden
        ui.start() #interaktive Benutzerobfläche starten

if __name__ == "__main__":
    Application().run()

