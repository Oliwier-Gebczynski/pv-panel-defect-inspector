# Kontener analizy i integracja z .NET

Kontener to osobna, bezstanowa usługa obliczeniowa. Wywołuje istniejący
`main.py process`, bez zmian w `main.py` i `core/`. Obsługuje wszystkie cztery
dotychczasowe tryby. Obraz działa na CPU i nie wymaga GPU.

Przepływ danych:

```text
Użytkownik → aplikacja .NET → zapis oryginałów w bazie / magazynie plików
                          → POST /inspect do kontenera Python
                          ← ZIP: result.json + obrazy/filmy + opcjonalny PDF
                          → zapis wyników i statusu w bazie
```

Kontener nie łączy się z bazą i nie przechowuje wyników między żądaniami.
Odpowiedź jest synchroniczna: przychodzi po zakończeniu całej analizy.

## Uruchomienie

1. Umieść **własne wytrenowane wagi** w następujących lokalizacjach:

   ```text
   core/detection/models/
   ├── panel_detector_gpu_thermal/weights/best.pt
   ├── panel_detector_gpu/weights/best.pt
   └── panel_defect_thermal/weights/best.pt
   ```

   Wagi są ignorowane przez Git i nie są dołączane do obrazu. Compose montuje
   ten katalog tylko do odczytu. Obecny detektor ładuje wszystkie trzy modele
   także w trybie wyłącznie termowizyjnym, więc potrzebne są wszystkie trzy pliki.
   Konto uruchamiające usługę w kontenerze (UID 10001) musi móc je odczytać.

2. Z katalogu projektu uruchom:

   ```bash
   docker compose up --build -d
   curl --fail http://localhost:8000/health
   curl --fail http://localhost:8000/ready
   ```

   `GET /health` sprawdza działanie HTTP; `GET /ready` dodatkowo sprawdza obecność
   wag i zwraca `503` z listą brakujących plików. Nie wykonuje próbnej inferencji.
   Dokumentacja interaktywna jest pod `http://localhost:8000/docs`.

   Domyślnie port jest dostępny wyłącznie lokalnie. Jeśli .NET także działa
   w Compose, dołącz usługę do tego samego pliku/sieci i użyj adresu
   `http://inspector:8000` zamiast `localhost`.

   Zatrzymanie:

   ```bash
   docker compose down
   ```

Alternatywnie bez Compose:

```bash
docker build -t pv-inspector .
docker run --rm --init -p 127.0.0.1:8000:8000 \
  --mount type=bind,src="$(pwd)/core/detection/models",dst=/app/core/detection/models,readonly \
  pv-inspector
```

## Dane wejściowe

`POST /inspect`, typ `multipart/form-data`:

| Pole | Typ | Znaczenie |
| --- | --- | --- |
| `mode` | tekst | Domyślnie `photo-thermal`; również `photo-rgb-thermal`, `video-thermal`, `video-rgb-thermal` |
| `thermal` | plik | Zawsze wymagany obraz/film termowizyjny |
| `rgb` | plik | Wymagany w obu trybach RGB |
| `calibration` | plik JSON | Wymagany w obu trybach RGB, wynik istniejącego `calibrate.py` |

W trybach wyłącznie termowizyjnych nie przesyłaj `rgb` ani `calibration`.
Zdjęcia: JPG/JPEG, PNG, BMP, TIF/TIFF. Filmy: MP4, AVI, MOV, MKV
(możliwość odczytu zależy także od kodeka). Wejścia są sprawdzane przez OpenCV.
Jeden request oznacza jedno zdjęcie/film termowizyjny i opcjonalnie odpowiadający
mu obraz RGB. Dla wielu zdjęć wyślij oddzielne żądania.

Zdjęcie termowizyjne:

```bash
curl --fail-with-body -X POST http://localhost:8000/inspect \
  -F 'mode=photo-thermal' \
  -F 'thermal=@data/processed/solo_thermal.png' \
  --output results.zip
unzip results.zip -d inspection-result
```

Zdjęcie RGB + termowizyjne:

```bash
curl --fail-with-body -X POST http://localhost:8000/inspect \
  -F 'mode=photo-rgb-thermal' \
  -F 'thermal=@data/processed/thermal.jpg' \
  -F 'rgb=@data/processed/rgb.jpg' \
  -F 'calibration=@data/metadata/calibration.json' \
  --output results.zip
```

Kalibrację wykonaj wcześniej lokalnie istniejącym `calibrate.py` — wymaga okien
graficznych. Użyj kalibracji odpowiedniej dla swojej pary kamer/rozdzielczości.

## Wynik

Sukces: HTTP `200`, `Content-Type: application/zip`. Nagłówek `X-Request-ID`
pozwala znaleźć wywołanie w `docker compose logs inspector`.
Archiwum zawiera wygenerowane pliki, ze ścieżkami względnymi, np.:

```text
result.json
report.pdf                           # jeśli wykryto defekty i utworzono raport
detection/thermal_processed.jpg      # dla zdjęcia
detection/crops/..._thermal.jpg      # wycinki paneli z defektami
overlay.jpg                          # dla zdjęcia RGB + thermal
```

Filmy zachowują istniejące nazwy wyników (`5fps_thermal.mp4`,
`detection/5fps_thermal_processed.mp4`, opcjonalnie `overlay.mp4`),
a archiwum zawiera również metadane i pozostałe wygenerowane pliki pośrednie.
Wejściowe oryginały nie są dołączane.

Przykład `result.json`:

```json
{
  "schema_version": 1,
  "request_id": "2db0049827664e469b99c07e599fa573",
  "status": "completed",
  "mode": "photo-thermal",
  "duration_seconds": 3.218,
  "saved_defect_panels": 1,
  "report": "report.pdf",
  "files": [
    "detection/crops/thermal_panel_0_defect_thermal.jpg",
    "detection/thermal_processed.jpg",
    "report.pdf"
  ]
}
```

`files` wylicza artefakty poza samym `result.json`. `saved_defect_panels` liczy
zapisane termowizyjne wycinki paneli, a nie pojedyncze plamki, klasy defektów
czy wszystkie uszkodzone panele w instalacji. Dla filmów obowiązuje dotychczasowa
logika usuwania powtórzeń. Dotychczasowy kod nie udostępnia współrzędnych,
klas ani confidence jako JSON; ten adapter ich nie dorabia.

Przy braku wykrytych defektów analiza nadal kończy się sukcesem,
`saved_defect_panels` wynosi `0`, a `report` ma wartość `null`. Istniejący
generator nie tworzy wówczas PDF. Logika detekcji, progi i zawartość raportu
pozostają takie jak w projekcie.

Błędy mają format JSON z polem `detail`:

| HTTP | Znaczenie |
| --- | --- |
| `413` | Suma rozmiarów plików przekracza limit |
| `422` | Brak wymaganych pól, nieobsługiwany tryb/format, puste lub nieczytelne dane, błędna kalibracja |
| `503` | Brak wag modeli lub kontener już analizuje inne żądanie; zajętość ma `Retry-After: 5` |
| `504` | Przekroczono czas analizy |
| `500` | Błąd istniejącego procesu analizy albo brak lub nieczytelność wymaganych wyników |

## Przykład klienta .NET

Poniższy fragment można wywołać z serwisu aplikacji lub workera .NET.
`thermalPath` wskazuje lokalnie zapisany oryginał; docelowo może to być też
strumień z magazynu plików. Adres usługi umieść w konfiguracji aplikacji.

```csharp
using System.IO.Compression;
using System.Net.Http;
using System.Text.Json;

static async Task<JsonDocument> InspectAsync(
    HttpClient client, string thermalPath, string zipPath,
    CancellationToken cancellationToken)
{
    using var form = new MultipartFormDataContent();
    form.Add(new StringContent("photo-thermal"), "mode");
    form.Add(new StreamContent(File.OpenRead(thermalPath)),
        "thermal", Path.GetFileName(thermalPath));

    using var request = new HttpRequestMessage(HttpMethod.Post, "inspect") { Content = form };
    using var response = await client.SendAsync(
        request, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
    if (!response.IsSuccessStatusCode)
    {
        var error = await response.Content.ReadAsStringAsync(cancellationToken);
        throw new HttpRequestException($"Inspector: {(int)response.StatusCode}: {error}");
    }

    await using (var output = File.Create(zipPath))
        await response.Content.CopyToAsync(output, cancellationToken);

    using var archive = ZipFile.OpenRead(zipPath);
    var entry = archive.GetEntry("result.json")
        ?? throw new InvalidDataException("Missing result.json");
    using var manifest = entry.Open();
    return await JsonDocument.ParseAsync(manifest, cancellationToken: cancellationToken);
}

using var client = new HttpClient
{
    BaseAddress = new Uri("http://localhost:8000/"),
    Timeout = TimeSpan.FromMinutes(16) // dłuższy niż domyślny limit kontenera
};
using var result = await InspectAsync(
    client, "thermal.jpg", "results.zip", CancellationToken.None);
Console.WriteLine(result.RootElement.GetProperty("saved_defect_panels").GetInt32());
// Zapisz result.json oraz wybrane pliki z ZIP w swojej bazie/magazynie plików.
```

W aplikacji użyj klienta zarządzanego przez `IHttpClientFactory`. Dla RGB dodaj
do formularza strumienie `rgb`, `calibration` i zmień `mode`.
Przy zapisie do bazy możesz zachować cały ZIP lub odczytać konkretne wpisy
przez `ZipArchive`, np. `report.pdf`. Nie zakładaj, że PDF zawsze istnieje.

## Konfiguracja i skalowanie

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MAX_UPLOAD_MB` | `100` | Maksymalna suma wielkości plików jednego żądania (MiB) |
| `PROCESS_TIMEOUT_SECONDS` | `900` | Maksymalny czas procesu `main.py` w sekundach |

Limit plików jest sprawdzany po odczytaniu formularza multipart. Przy wdrożeniu
ustaw również limit całego body i timeout na reverse proxy. Zapewnij miejsce
w `/tmp` na pliki wejściowe, wyniki i ZIP. Po wysłaniu odpowiedzi lub błędzie
katalog danego żądania jest usuwany; restart kontenera przerywa bieżącą analizę.

Jedna kopia przyjmuje jedną analizę naraz. Kolejna dostaje `503`; .NET może
ponowić ją z opóźnieniem. Każda analiza uruchamia osobny proces i ponownie
ładuje modele — to celowy kompromis pozwalający zachować obecną implementację.

Więcej kopii kontenera może działać za load balancerem z tymi samymi wagami.
Każda kopia potrzebuje własnej pamięci na modele. Do skalowania konfigurację
portu hosta z przykładowego Compose zastąp wewnętrzną siecią i load balancerem;
stałe mapowanie `8000:8000` nie nadaje się do replik na jednym hoście.
Nie zwiększaj liczby workerów Uvicorn, jeśli chcesz zachować limit jednej
analizy na kontener (semafor działa w obrębie procesu).

Dla długich analiz .NET może zapisać zadanie w bazie i obsłużyć je w workerze
z kolejki, a użytkownikowi od razu zwrócić identyfikator. Kontener dalej
obsługuje ten sam `POST /inspect`; kolejka i trwałe statusy należą do aplikacji
.NET. Tutaj nie są implementowane. Usługa powinna być wywoływana przez backend
w prywatnej sieci; nie zawiera logowania użytkowników.

## Sprawdzenie adaptera bez modeli

```bash
python3 -m venv /tmp/pv-inspector-tests
/tmp/pv-inspector-tests/bin/pip install -r tests/requirements.txt
/tmp/pv-inspector-tests/bin/python -m pytest tests -q
```

Testy zastępują inferencję atrapą. Sprawdzają kontrakt HTTP/ZIP, izolację,
sprzątanie, walidację, zajętość i błędy procesu. Faktyczna inferencja wymaga
oryginalnych wag i odpowiednich danych wejściowych.

Referencje interfejsu: [multipart i UploadFile w FastAPI](https://fastapi.tiangolo.com/tutorial/request-files/),
[budowanie obrazów Docker](https://docs.docker.com/build/building/best-practices/).
