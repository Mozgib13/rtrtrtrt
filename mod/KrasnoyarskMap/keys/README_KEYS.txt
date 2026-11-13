В эту папку при сборке мода положите Krasnoyarsk.bikey
(публичный ключ, которым подписаны PBO карты).

Ключи создаются так (на ПК с DayZ Tools, однократно):

  1. Найти DSCreateKey.exe — обычно:
     "<Steam>\steamapps\common\DayZ Tools\Bin\DsUtils\DSCreateKey.exe"
     (если путь другой — откройте папку DayZ Tools и найдите файл по имени DSCreateKey.exe).
  2. Выполнить:
        DSCreateKey.exe Krasnoyarsk
  3. Получите два файла:
        Krasnoyarsk.biprivatekey  — ПРИВАТНЫЙ. Никому не показывать, не выкладывать,
                                    не коммитить в git. Только для сборки (.bisign).
        Krasnoyarsk.bikey         — ПУБЛИЧНЫЙ. Кладётся сюда и в keys\ на сервере.
  4. Каждый PBO карты подписывается:
        DSSignFile.exe Krasnoyarsk.biprivatekey Krasnoyarsk_world.pbo
     → рядом появится Krasnoyarsk_world.pbo.Krasnoyarsk.bisign
     Повторить для data и navmesh.

ВАЖНО:
- .biprivatekey не распространяется. Если он утёк — перевыпустите ключи
  и подпишите PBO заново.
- Без .bikey в keys\ на сервере и без .bisign рядом с PBO сервер
  с verifySignatures=2 откажется загружать мод.
