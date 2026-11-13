# 03. Пересборка исходников (по желанию)

Готовые файлы уже лежат в `source/` и `previews/`. Python вам понадобится,
только если захотите изменить рельеф, дороги, сиды генерации или размеры.

## Запуск

```bash
cd rtrtrtrt
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux/macOS
pip install -r tools/requirements.txt
python tools/generate_terrain.py
```

Скрипт детерминирован (фиксированные сиды): одинаковый код → одинаковые файлы.

## Что получается на выходе

| Файл | Для чего |
|---|---|
| `source/heightmap.asc` | **Импортируется в Terrain Builder** (File → Import → Terrains). Esri ASCII Grid, 2048×2048, ячейка 6.0 м, северная строка первой, `xllcorner 200000` |
| `source/heightmap.png` | 16-бит серый бэкап рельефа (0 → −4 м, 65535 → +235 м) |
| `source/heightmap.legend.txt` | Шпаргалка по нормализации высот |
| `source/satmask.png` | Маска поверхности 4096² (цвет → слой в `layers.cfg`) |
| `source/satmap.png` | Стилизованная спутниковая текстура 4096² (базовая раскраска земли) |
| `source/maplegend.png` | Легенда цветов маски |
| `source/layers.cfg` | Определения слоёв TB: цвет → текстуры ванильного DayZ (`DZ\surfaces...`, `DZ\surfaces_bliss...`) |
| `docs/09-coordinates.md` | Сгенерированная таблица POI (X/Z/высота): мосты, бункеры, аэродром, остров |
| `mission/dayzOffline.krasnoyarsk/cfgeventspawns.xml` | Точки лута/машин/меддропов (на дорогах и суше) |
| `mission/dayzOffline.krasnoyarsk/cfgplayerspawnpoints.xml` | 120 пузырей спавна игроков |
| `previews/relief.png` | Отмывка рельефа + горизонтали |
| `previews/satellite.png` | Превью сателлита с подписями |
| `previews/mask.png` | Превью маски |

## Что обычно меняют в скрипте (`tools/generate_terrain.py`)

- `WORLD_M`, `GRID`, `CELL` — размер мира и шаг сетки (соотношения 6 м при 2048 — оптимальны).
- `ROADS` — список дорог (имя, ширина м, точки X/Z). Мосты — тоже дороги.
- `URBAN` — полигоны застройки (влияют на маску «бетон» и спутник).
- `PILLARS`, `BUNKERS`, `LAKES`, `KACHA` — скалы, бункеры, озёра, приток.
- `SEED` — другая случайность (шум, лес). После смены обязательно перегенерируйте
  И проверьте `previews/` глазами.

## Если что-то поехало

- Памяти не хватает на слабых машинах — уменьшите `MASK_PX` до 2048.
- Скрипт и так ест ~1.5 ГБ в пике; закрывать просмотрщик картинок не обязательно,
  но свободная память нужна.

Дальше: `docs/04-terrain-builder.md`.
