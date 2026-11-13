# 04. Terrain Builder: импорт и сборка мира

Всё ниже делается на Windows с DayZ + DayZ Tools. Время операции — от 20 минут
(первая сборка) до 3–6 часов (наполнение города — это уже работа в редакторе, её не ускорить).

## 4.0 Подготовка папок

Создайте структуру на смонтированном P: диске:

```
P:\Krasnoyarsk\
  source\          ← сюда ВСЕ файлы из source\ этого репозитория (heightmap.asc, satmask.png, satmap.png, maplegend.png, layers.cfg, heightmap.png, heightmap.legend.txt)
  source\TerrainBuilder\   ← (создастся сам, там будут .tv4p/.tml)
  world\           ← сюда потом положите addon_templates\world\config.cpp
  data\            ← сюда addon_templates\data\config.cpp
  navmesh\         ← сюда addon_templates\navmesh\config.cpp
```

Скопируйте репозиторий (или только `source\` + `mod\addon_templates\`) на машину с DayZ Tools.

## 4.1 Терраин-билдер: настройка Buldozer

`DayZ Tools → Terrain Builder → Tools → Preferences… → Buldozer`:

- **.exe file path**: `D:\Steam\steamapps\common\DayZ\DayZ_BE.exe` (подставьте свой путь к DayZ)
- **Launch Parameters**: `-buldozer -window -exThreads=0 -mod= -noAsserts -nologs -profiles=P:\Buldozer -cfg=P:\Buldozer\Buldozer.cfg -name=Buldozer`
- **Data Directory**: `P:\`

Проверьте: `View → Buldozer` — откроется превью (пока пустой мир).

## 4.2 Импорт высот

1. `File → Import → Terrains (xyz file)…` → выберите `P:\Krasnoyarsk\source\heightmap.asc`.
2. В Layers Manager найдите слой с heightmap → ПКМ → **Terrain Coordinates and Properties**:
   - **Easting: 200000**, **Northing: 0**
   - Size: автоматически (2048 × 6 = **12288 m**).
3. Нажмите OK, затем кнопку **Fit to view** (иначе терраин «улетел» за пределы вида).

Высота в файле — в метрах (от −3.1 до +153): TB подхватит диапазон автоматически.

## 4.3 Импорт маски поверхностей и спутника

1. `File → Import → Surface Mask Images…` → `P:\Krasnoyarsk\source\satmask.png`.
   ПКМ по слою → **Terrain Coordinates and Properties**:
   - Easting **200000**, Northing **0**
   - **Size width/height: 12288 × 12288** (НЕ 4096 — это метры!)
2. `File → Import → Satellite Images…` → `P:\Krasnoyarsk\source\satmap.png`.
   Свойства аналогично: easting 200000, northing 0, размер **12288**.

> Если после этого сателлит и рельеф «зеркалят» друг друга по вертикали
> (сравните изгиб реки с `previews/relief.png`) — переверните satmask/satmap
> по вертикали в GIMP (Image → Transform → Flip Vertical) и импортируйте заново.
> Рельеф при этом НЕ переворачивайте.

## 4.4 Повреждение: Rebuild Terrain

1. Окно **MapFrames** → «add mapframe» → OK.
2. ПКМ по новому MapFrame → **Properties**:
   - **Name**: `Krasnoyarsk`
   - **Project root dir**: `P:\Krasnoyarsk\source`
   - Нажмите **Create subfolders**, OK.
3. Вкладка **Samplers**:
   - Terrain sampler: grid size **2048 × 2048**, cell size **6**
   - Satellite/surface mask source images: size **4096** px
   - Texture layer: size **40 × 40 m** (должно быть ≥ 2× ячейки)
4. Вкладка **Processing**:
   - нажать «…» и указать `P:\Krasnoyarsk\source\layers.cfg`
   - (адреса текстур в layers.cfg ссылаются на ванильные `DZ\...` — менять не нужно)
   - **Rebuild Terrain** → Yes.
5. MapFrames → ваш проект → ПКМ → **Rebuild Terrain** (то же самое из меню —
   генерирует терраин по импортированному heightmap.asc).
6. Вкладка **Processing** → отметьте **Export satellite texture** и
   **Export surface mask** (4 materials per cell) → **Generate Layers** → дождитесь конца.
   В `P:\Krasnoyarsk\source\` появится папка слоёв (`layers\*.png`).

## 4.5 Экспорт мира (.wrp)

1. MapFrames → ПКМ → **Export** → **Terrain** (или **World**, зависит от версии TB).
2. Укажите выход: `P:\Krasnoyarsk\world\`.
   Получите `Krasnoyarsk.wrp` (сотни МБ — это нормально).
3. Скопируйте `mod\addon_templates\world\config.cpp` → `P:\Krasnoyarsk\world\config.cpp`
   (он уже подготовлен: `worldName="\Krasnoyarsk\world\Krasnoyarsk.wrp"`, координаты центра карты,
   подписи объектов и т.д., см. `docs/05-world-setup.md`).
4. Создайте `$PBOPREFIX$` в каждой из трёх папок (`world`, `data`, `navmesh`),
   см. `mod\addon_templates\README.md`.

## 4.6 Первый взгляд в Buldozer

`View → Buldozer` (или кнопка). Летайте над картой (W,A,S,D; R/E — высота; Esc — выход):

- Енисей течёт с юга на север, русло синее, остров посередине (z≈5.2–7.0 км);
- городские «поля» серые, дороги тёмные, мосты читаются;
- Столбы на юго-востоке — скальный кряж;
- на северо-западе — аэродром; на северо-востоке — впадение Качи;
- бункерные ямы — три квадратных углубления (B1≈z 1600, B2≈z 2560, B3≈z 8660 — высоты дна в docs/09-coordinates.md).

Если вода не видна — вы смотрите с большой высоты либо ocean-материал не найден:
сверьте `oceanMaterial*` в `world\config.cpp` с ванильным `P:\DZ\worlds\chernarusplus\config.cpp`.

Дальше: `docs/05-world-setup.md` (объекты, navmesh, подписи), затем `docs/06-pbo-build.md`.
