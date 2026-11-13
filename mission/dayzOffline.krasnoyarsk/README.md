# mpmissions: dayzOffline.krasnoyarsk

Это папка миссии для сервера с картой Krasnoyarsk. Она НЕ самодостаточна —
так устроены все кастомные карты DayZ.

## Что уже сгенерировано (и можно использовать как есть)

- `cfgeventspawns.xml` — все позиции выбраны генератором на суше и НА ДОРОГАХ:
  - `Loot` — статические точки лута внутри городской застройки (156 точек);
  - `VehicleCivilianCars` — легковые машины на дорогах (70);
  - `VehicleTrucks` — грузовики у промзоны / аэропорта / дорог (38);
  - `StaticMedDrop` — «медицинские» ящики у бункеров и промышленных точек (8);
  - `ItemWoodenPlanks` — несколько точек досок.
- `cfgplayerspawnpoints.xml` — 120 «пузырей» спавна свежего выжившего
  (дороги, городские кварталы, остров, аэропорт, бункеры).

> Если вы перегенерировали рельеф скриптом (`python tools/generate_terrain.py`),
> эти файлы обновятся автоматически.

## Как установить на сервер

1. Скопируйте ванильную миссию из сервера:
   `mpmissions\dayzOffline.chernarusplus\` → `mpmissions\dayzOffline.krasnoyarsk\`.
   В ней лежат ВСЕ нужные файлы: `db\types.xml` (полный лут), `db\events.xml`,
   `db\globals.xml`, `db\economy.xml`, `cfgeconomycore.xml`, `cfgspawnabletypes.xml`
   и т.д. Не трогайте их — лут/экономика останутся ванильными.
2. ЗАМЕНИТЕ в `mpmissions\dayzOffline.krasnoyarsk\` два файла из ЭТОЙ папки:
   - `cfgeventspawns.xml`
   - `cfgplayerspawnpoints.xml`
3. В `serverDZ.cfg` укажите:
   ```cpp
   class Missions { class DayZ { template = "dayzOffline.krasnoyarsk"; }; };
   ```
4. Запустите сервер — сначала на `verifySignatures = 0` ТОЛЬКО для проверки,
   потом верните `2`.

## Зомби (ininfected) — почему их пока не будет

Позиции спавна зомби привязаны к ЗДАНИЯМ через `mapgrouppos.xml`
(координаты каждого здания + тип строения) и `mapgroupproto.xml`.
Пока вы не поставили дома в Terrain Builder, зомби негде спавниться —
сервер при этом работает нормально, просто без зомби.

Когда дома будут расставлены:

1. Возьмите В КАЧЕСТВЕ ОБРАЗЦА `mapgroupproto.xml` / `mapgroupcluster.xml` /
   `mapgrouppos.xml` из `mpmissions\dayzOffline.chernarusplus\` сервера.
2. В `mapgrouppos.xml` пропишите координаты своих зданий (тип `building`
   должен совпадать с именами из `mapgroupproto.xml`).
3. Перезапустите сервер.

## Животные (медведи/кабаны/волки)

Ванильные `env\*_territories.xml` привязаны к координатам Черноруси.
Их координаты у вас будут «в другом климатическом районе». Пока — без животных
(сервер работает), либо перенесите точки вручную в свои координаты из `docs/09-coordinates.md`.
