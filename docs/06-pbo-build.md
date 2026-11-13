# 06. Сборка PBO и подписание ключом

Цель: получить `@KrasnoyarskMap` — папку мода со структурой, которую примут и клиент, и сервер.

## 6.1 Итоговая структура папки мода

```
@KrasnoyarskMap\
  mod.cpp                          ← лежит в этом репозитории: mod\KrasnoyarskMap\mod.cpp
  Addons\
    Krasnoyarsk_world.pbo
    Krasnoyarsk_world.pbo.Krasnoyarsk.bisign
    Krasnoyarsk_data.pbo
    Krasnoyarsk_data.pbo.Krasnoyarsk.bisign
    Krasnoyarsk_navmesh.pbo
    Krasnoyarsk_navmesh.pbo.Krasnoyarsk.bisign
  keys\
    Krasnoyarsk.bikey
```

`.bisign` имя строится как `<pbo>.<keyname>.bisign` — регистр важен.

## 6.2 Ключи (один раз на весь проект)

На машине с DayZ Tools:

```cmd
"<...путь к DayZ Tools>\Bin\DsUtils\DSCreateKey.exe" Krasnoyarsk
```

→ `Krasnoyarsk.biprivatekey` (СЕКРЕТНЫЙ) и `Krasnoyarsk.bikey` (публичный).

- `Krasnoyarsk.biprivatekey` — храните как пароль: не выкладывайте, не коммитьте,
  не отправляйте игрокам/серверу. Положите в менеджер паролей.
- `Krasnoyarsk.bikey` — включите в репозиторий/сборку: он безопасен.
  (Можете положить его и в `mod\KrasnoyarskMap\keys\` локально, но в git не отправляйте лишний раз.)

## 6.3 Упаковка (RaG PBO Builder — самый простой путь)

1. Скачайте и запустите **RaG PBO Builder** (https://github.com/Tyson89/RaG-PBO-Builder).
2. **Project Source**: например `P:\Krasnoyarsk\_staging\world` — предварительно
   скопируйте туда содержимое `P:\Krasnoyarsk\world\` (или укажите папку напрямую —
   на усмотрение, см. подсказки утилиты).
3. **Build Output**: папка `@KrasnoyarskMap\Addons\` (создайте заранее).
4. В **Options** проверьте пути к DayZ Tools:
   - `binarize.exe`, `CfgConvert.exe`, `ImageToPAA.exe`, `DSSignFile.exe`.
5. Включите **Update PAA** (PNG слоёв → PAA автоматически) и **Convert configs to config.bin**.
6. Выберите аддон `Krasnoyarsk_world` → **Build PBOs**. Повторите для `Krasnoyarsk_data` и `Krasnoyarsk_navmesh`.
7. RaG сам подпишет PBO (укажите свой `Krasnoyarsk.biprivatekey` в опциях) и вернёт .bisign.
   Если подписи не прошли — подпишите вручную (6.4).

Частые грабли: неправильно указанный **Project Source** → PBO соберётся с неверными
внутренними путями → игра не найдёт мир (см. FAQ «Can't load world»).

## 6.4 Подписание вручную (если нужно)

```cmd
"<...>\Bin\DsUtils\DSSignFile.exe" Krasnoyarsk.biprivatekey Krasnoyarsk_world.pbo
"<...>\Bin\DsUtils\DSSignFile.exe" Krasnoyarsk.biprivatekey Krasnoyarsk_data.pbo
"<...>\Bin\DsUtils\DSSignFile.exe" Krasnoyarsk.biprivatekey Krasnoyarsk_navmesh.pbo
```

## 6.5 Локальная проверка до сервера

1. Скопируйте `@KrasnoyarskMap` в папку клиента DayZ
   (`<Steam>\steamapps\common\DayZ\`).
2. Запустите игру с параметром: `-mod=@KrasnoyarskMap`
   (или через DayZ Launcher → Mods → «DayZ (Krasnoyarsk)» → Play).
3. В главном меню при наведении на «Играть» игра покажет требуемые моды —
   должна быть строка **Krasnoyarsk Map** без предупреждений о подписи.
4. Самый надёжный тест — локальный выделенный сервер на этой же машине
   (см. `docs/07-server.md`): так вы проверяете и PBO, и подпись, и миссию.
   Клиентом с `-mod=@KrasnoyarskMap` подключитесь к `127.0.0.1:2302`.

Если мод не грузится и игра пишет про подпись — смотрите `docs/10-faq.md`.

Дальше: `docs/07-server.md`.
