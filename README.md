# PV Panel Defect Inspector

## Opis

**PV Panel Defect Inspector** to narzędzie do automatycznej inspekcji paneli fotowoltaicznych w celu wykrywania defektów. Aplikacja wykorzystuje obrazy i nagrania wideo z kamer termowizyjnych oraz RGB, aby zidentyfikować, zlokalizować i zaraportować uszkodzenia.

Projekt został zaprojektowany w sposób modułowy, umożliwiając łatwą rozbudowę i dostosowanie do różnych scenariuszy inspekcji.

## Funkcjonalności

- **Wykrywanie defektów**: Identyfikacja uszkodzeń na panelach na podstawie modeli AI (YOLO).
- **Obsługa wielu formatów**: Przetwarzanie zarówno nagrań wideo, jak i pojedynczych zdjęć.
- **Tryby pracy**:
    - Wideo: RGB + Termowizja
    - Wideo: Tylko termowizja
    - Zdjęcie: RGB + Termowizja
    - Zdjęcie: Tylko termowizja
- **Kalibracja kamer**: Interaktywny proces kalibracji w celu dopasowania obrazów z kamery RGB i termowizyjnej.
- **Fuzja obrazów**: Generowanie nagrań i zdjęć z nałożonymi na siebie obrazami z obu kamer w celu lepszej wizualizacji.
- **Raportowanie**: Automatyczne tworzenie raportów w formacie PDF zawierających wykryte defekty.

## Instalacja

### Kontener i integracja z aplikacją .NET

Gotowy kontener udostępnia `POST /inspect`: przyjmuje zdjęcie/film przez HTTP
i zwraca ZIP z wynikami, podsumowaniem JSON oraz PDF, jeśli wykryto defekty.
Instrukcja uruchomienia, format danych i przykład klienta C# znajdują się
w [docs/container.md](docs/container.md). Istniejący sposób uruchamiania pozostaje dostępny.

1. Sklonuj repozytorium:
   ```bash
   git clone <adres-repozytorium>
   cd pv-panel-defect-inspector
   ```

2. Zainstaluj wymagane biblioteki Pythona. Zalecane jest użycie wirtualnego środowiska.
   ```bash
   pip install opencv-python numpy ultralytics fpdf scipy
   ```

## Użycie

### Kalibracja

Przed pierwszym uruchomieniem procesu inspekcji z użyciem obu kamer (RGB i termowizyjnej) konieczne jest przeprowadzenie kalibracji. Służy do tego skrypt `calibrate.py`.

**Polecenie:**
```bash
python calibrate.py --thermal-input <sciezka_do_zdjecia_thermal> --rgb-input <sciezka_do_zdjecia_rgb> --calibration-file <sciezka_do_zapisu_kalibracji.json>
```

- `--thermal-input`: Ścieżka do zdjęcia termowizyjnego.
- `--rgb-input`: Ścieżka do odpowiadającego mu zdjęcia RGB.
- `--calibration-file` (opcjonalnie): Ścieżka do zapisu pliku kalibracji (domyślnie `calibration.json`).

Po uruchomieniu polecenia wyświetlą się dwa okna, w których należy zaznaczyć ten sam obszar (panel) na obu zdjęciach. Po zakończeniu zostanie wygenerowany plik kalibracyjny.

### Przetwarzanie (Inspekcja)

Głównym punktem wejścia do analizy jest skrypt `main.py`.

**Polecenie:**
```bash
python main.py process --mode <tryb> --thermal-input <sciezka_do_pliku_thermal> [--rgb-input <sciezka_do_pliku_rgb>] [--output-dir <katalog_wynikowy>] [--calibration-file <plik_kalibracji>]
```

**Argumenty:**

- `--mode`: Tryb przetwarzania. Dostępne opcje:
    - `video-rgb-thermal`: Analiza nagrania wideo z obu kamer.
    - `video-thermal`: Analiza nagrania tylko z kamery termowizyjnej.
    - `photo-rgb-thermal`: Analiza zdjęcia z obu kamer.
    - `photo-thermal`: Analiza zdjęcia tylko z kamery termowizyjnej.
- `--thermal-input`: Ścieżka do pliku wejściowego (wideo lub obraz) z kamery termowizyjnej.
- `--rgb-input`: Ścieżka do pliku wejściowego (wideo lub obraz) z kamery RGB. Wymagany dla trybów `*-rgb-thermal`.
- `--output-dir` (opcjonalnie): Katalog, w którym zostaną zapisane wyniki (domyślnie `results`).
- `--calibration-file` (opcjonalnie): Ścieżka do pliku kalibracji (domyślnie `calibration.json`). Jeśli plik nie zostanie znaleziony, aplikacja poinformuje o konieczności jego wygenerowania.

#### Fuzja wideo (Overlay)

Tryb `video-rgb-thermal` generuje wideo z nałożoną warstwą termowizyjną na obraz RGB. Wynikowy plik `overlay.mp4` znajdzie się w katalogu wyjściowym. Warstwa termowizyjna jest automatycznie kolorowana w celu zwiększenia kontrastu.

**Przykłady użycia:**

1. **Analiza wideo z obu kamer:**
   ```bash
   python main.py process --mode video-rgb-thermal --thermal-input data/raw/thermal.mp4 --rgb-input data/raw/rgb.mp4 --output-dir results_video
   ```

2. **Analiza zdjęcia termowizyjnego:**
   ```bash
   python main.py process --mode photo-thermal --thermal-input data/raw/thermal_shot.jpg --output-dir results_photo_thermal
   ```

## Struktura projektu

```
.
├── core/                 # Główna logika aplikacji
│   ├── detection/        # Wykrywanie defektów (modele, skrypty)
│   ├── reporting/        # Generowanie raportów
│   └── video_processing/ # Przetwarzanie wideo i obrazów
├── data/                 # Dane (wejściowe, przetworzone, metadane)
├── tools/                # Narzędzia pomocnicze
├── main.py               # Główny skrypt uruchomieniowy
├── calibrate.py          # Skrypt do kalibracji kamer
└── README.md             # Ten plik
```

python calibrate.py --thermal-input data/processed/thermal_video.mp4 --rgb-input data/processed/rgb_video.mp4

python calibrate.py --thermal-input data/processed/thermal.jpg --rgb-input data/processed/rgb.jpg --calibration-file calibrate.json

python main.py process --mode video-rgb-thermal --thermal-input data/processed/thermal_video.mp4 --rgb-input data/processed/rgb_video.mp4 --output-dir results_video --calibration-file data/metadata/calibration.json

python main.py process --mode photo-rgb-thermal --thermal-input data/processed/thermal.jpg --rgb-input data/processed/rgb.jpg --output-dir results_video --calibration-file data/metadata/calibration.json

python main.py process --mode photo-thermal --thermal-input data/processed/solo_thermal.png --output-dir results

curl --fail-with-body http://localhost:8000/inspect \
  -F 'mode=photo-thermal' \
  -F 'thermal=@/home/opg/Documents/Github/pv-panel-defect-inspector/data/solo_thermal.png' \
  --output inspection.zip