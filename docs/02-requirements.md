# 02. Что понадобится (требования)

## Обязательно (Windows ПК)

| Что | Зачем | Где взять |
|---|---|---|
| **DayZ** (Steam, app 221100) | Игра, для проверки карты в одиночке + клиент для сервера | Ваша библиотека Steam |
| **DayZ Tools** (Steam, app 830640, бесплатно) | Terrain Builder, World Editor (Buldozer), Binarize, DSSignFile/DSCreateKey | Steam → Library → Tools → DayZ Tools → Install |
| **DayZ Server** (через SteamCMD, app 223350) | Dedicated server | `steamcmd +login anonymous +app_update 223350 validate +quit` |
| ~30 GB свободного места | P: диск монтирует все игровые данные | SSD желательно |

DayZ и DayZ Tools должны стоять на **одном диске** (иначе P: диск может не смонтироваться).

## Для подписи PBO (выберите одно)

- **RaG PBO Builder** — бесплатный, open source, Windows: https://github.com/Tyson89/RaG-PBO-Builder
  (удобный GUI, умеет сам вызывать Binarize/DSSignFile из DayZ Tools, конвертировать PNG→PAA).
- **Mikero's DePbo Tools** — классика коммьюнити: https://armaholic.com/page.php?id=11030
  (pboProject + DSCreateKey/DSSignFile; shareware, но рабочий).
- Термин «Addon Builder» из DayZ Tools сообщество не рекомендует для подписи/бинаризации
  (ломает RVMAT/текстуры) — для правки config.cpp текстовым редактором он не нужен вообще.

## Необязательно (для пересборки исходников)

- **Python 3.10+** + `pip install -r tools/requirements.txt` (numpy, pillow, matplotlib).
  Нужен только если захотите поменять рельеф/дороги/сиды. Сам по себе репозиторий
  содержит уже сгенерированные файлы — можно собрать карту вообще без Python.

- **GIMP** (бесплатно) — если захотите подкрасить `satmap.png`/`satmask.png` вручную.

## Для сервера

- Server machine: Windows/Linux, DayZ Server files, ~4 GB RAM на 60 слотов минимум,
  порт **UDP 2302** (и 2303, 2304 для Steam) открыт наружу.
- У вашего хостинга должны поддерживаться **кастомные моды через -mod=** и загрузка своих файлов
  (для self-hosted — без вопросов; для GPortal/Nitrado и т.п. — почти всегда, спросите поддержку,
  как загрузить папку мода и .bikey, образец ответа есть в `docs/07-server.md`).

## Проверьте заранее

1. Запустите **DayZ Tools** → `Tools > Workbench` — смонтируется диск **P:**
   (если был смонтирован криво — `Tools > Dismount Drive P`, затем Workbench снова).
2. Откройте `P:\DZ\` — должна быть иерархия игровых данных.
3. Откройте `P:\DZ\worlds\chernarusplus\config.cpp` в текстовом редакторе —
   рядом лежит эталон, на который будем равняться при сборке (oceanMaterial и т.д.).
