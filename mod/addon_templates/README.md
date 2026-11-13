# Шаблоны аддонов карты Krasnoyarsk

Три PBO-аддона, которые собираются из одного TB-проекта:

```
P:\Krasnoyarsk\
  world\    config.cpp (этот шаблон) + Krasnoyarsk.wrp + layers\*.paa после сборки
  data\     config.cpp (заглушка)   + layers\*.png/paa (если TB экспортирует слои сюда)
  navmesh\  config.cpp (заглушка)   + navmesh.nm (если генерировали navmesh)
```

## Шаги

1. После **Terrain Builder → Rebuild Terrain** экспортируйте результат в `P:\Krasnoyarsk\world\`.
2. Скопируйте `addon_templates/world/config.cpp` → `P:\Krasnoyarsk\world\config.cpp`.
3. Создайте в каждой папке файл `$PBOPREFIX$` (без расширения):
   - `P:\Krasnoyarsk\world\$PBOPREFIX$`  → содержимое: `Krasnoyarsk\world`
   - `P:\Krasnoyarsk\data\$PBOPREFIX$`   → содержимое: `Krasnoyarsk\data`
   - `P:\Krasnoyarsk\navmesh\$PBOPREFIX$`→ содержимое: `Krasnoyarsk\navmesh`
4. Упакуйте эти три папки в PBO (см. `docs/06-pbo-build.md`): `Krasnoyarsk_world.pbo`,
   `Krasnoyarsk_data.pbo`, `Krasnoyarsk_navmesh.pbo`.
5. Подпишите все три PBO одним ключом.

## Почему три аддона

Так устроен официальный шаблон кастомных террейнов DayZ: `world` держит CfgWorlds и
саму геометрию, `data` — сгенерированные слои текстур, `navmesh` — бинарную сетку
навигации для зомби. `worldName` в `world\config.cpp` обязан совпадать с префиксом
аддона `world`, иначе игра не найдёт мир.
