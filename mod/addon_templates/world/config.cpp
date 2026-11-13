// world/config.cpp — CfgWorlds for the Krasnoyarsk map (DayZ 1.30 / Enfusion era).
// Based on the community custom-terrain template (Project-Everglades / DayZ-Resources).
//
// Куда класть: скопируйте ЭТОТ файл в P:\Krasnoyarsk\world\config.cpp ПОСЛЕ экспорта
// мира из Terrain Builder (или прямо поверх того, что создал TB).
//
// Что можно безопасно менять:
//   - worldId (оставьте 2, если не знаете, какие номера заняты)
//   - класс Names (подписи объектов; если игра ругается — удалите класс Names целиком,
//     это только метки на карте)
//   - центр карты centerPosition, startTime и т.п.
//
// Что НЕ трогать без понимания:
//   - worldName должен совпадать с PBO-префиксом: \Krasnoyarsk\world\Krasnoyarsk.wrp
//   - oceanMaterial* — если вода в игре чёрная, скопируйте эти 3 строки из ванильного
//     конфига P:\DZ\worlds\chernarusplus\config.cpp (откройте в текстовом редакторе).

class CfgPatches
{
	class Krasnoyarsk
	{
		units[]={};
		weapons[]={};
		requiredVersion=0.1;
		requiredAddons[]={"DZ_Data","DZ_Surfaces","DZ_Surfaces_Bliss"};
		author="Krasnoyarsk Map Project";
		name="Krasnoyarsk";
		url="";
	};
};

class CfgWorlds
{
	class DefaultLighting;
	class CAWorld;
	class Chernarusplus: CAWorld
	{
		class Grid;
	};

	class Krasnoyarsk: Chernarusplus
	{
		worldId=2;
		cutscenes[]={};
		description="Krasnoyarsk — community map (12 x 12 km)";
		icon="";
		worldName="\Krasnoyarsk\world\Krasnoyarsk.wrp";
		pictureMap="";
		pictureShot="";

		// Вода. Значение из Everglades-шаблона; если вода чёрная — возьмите строки из
		// ванильного P:\DZ\worlds\chernarusplus\config.cpp (блок oceanMaterial).
		oceanMaterial="{11D1156E1D9DADF0}Graphics/Materials/water/oceanold_samplemap.emat";
		oceanNiceMaterial="{11D1156E1D9DADF0}Graphics/Materials/water/oceanold_samplemap.emat";
		oceanStormMaterial="{11D1156E1D9DADF0}Graphics/Materials/water/oceanold_samplemap.emat";

		plateFormat="ML$ - #####";
		plateLetters="ABCDEGHIKLMNOPRSTVXZ";
		longitude=92.87;
		latitude=56.02;

		class AISpawnerParams
		{
		};

		class OutsideTerrain
		{
			satellite="DZ\rocks\Data\MainTextures\terrain\cp_gravel_co.paa";
			enableTerrainSynth="true";
			class Layers
			{
				class Layer0
				{
					nopx="DZ\surfaces\data\terrain\cp_gravel_nopx.paa";
					texture="DZ\surfaces\data\terrain\cp_gravel_ca.paa";
				};
			};
		};

		class Grid: Grid
		{
			offsetX=0;
			offsetY=-12288;
			class Zoom1
			{
				zoomMax=0.5;
				format="XY";
				formatX="Aa";
				formatY="00";
				stepX=200;
				stepY=200;
			};
			class Zoom2
			{
				zoomMax=1e+030;
				format="XY";
				formatX="A";
				formatY="0";
				stepX=2000;
				stepY=2000;
			};
		};

		startTime="8:30";
		startDate="01/05/1985";
		startWeather=0.1;
		startFog=0;
		forecastWeather=0.30000001;
		forecastFog=0;
		seagullPos[]={6144,150,6144};
		centerPosition[]={6144,12,6144};

		// Иллюзионная «глиссада» для ИЛС-аэропорта Емельяново (ВПП курс 028°).
		// На геймплей не влияет — это точки для ИИ/сцен. Курс: (sin28°, 0, cos28°).
		ilsPosition[]={2500,9400};
		ilsDirection[]={0.469,0.000000,0.883};
		ilsTaxiIn[]={1990,8420,2500,9400,3060,10420};
		ilsTaxiOff[]={3060,10420,2500,9400,1990,8420};
		drawTaxiway="false";

		class ReplaceObjects
		{
		};
		class Sounds
		{
			sounds[]={};
		};
		class Animation
		{
			vehicles[]={};
		};
		class Lighting: DefaultLighting
		{
		};

		clutterGrid=1; // Default Value: 1.11
		clutterDist=125; // Default Value: 55
		noDetailDist=40;
		fullDetailDist=15;
		minTreesInForestSquare=3;
		minRocksInRockSquare=4;

		class Subdivision
		{
			class Fractal
			{
				rougness=5;
				maxRoad=0.02;
				maxTrack=0.5;
				maxSlopeFactor=0.050000001;
			};
			class WhiteNoise
			{
				rougness=2;
				maxRoad=0.0099999998;
				maxTrack=0.050000001;
				maxSlopeFactor=0.0024999999;
			};
			minY=-4;
			minSlope=0.02;
		};

		class Ambient
		{
		};

		// Подписи объектов на карте (необязательно).
		// Если после установки игра/сервер ругается на класс Names — просто удалите его целиком.
		class Names
		{
			class Center
			{
				name="CENTR";
				position[]={4700, 12, 5700};
			};
			class Tatyshev
			{
				name="ISLAND PARK";
				position[]={6144, 3, 6050};
			};
			class Sovetsky
			{
				name="SOVETSKY DISTRICT";
				position[]={7900, 12, 6300};
			};
			class Emelyanovo
			{
				name="EMELYANOVO AIRPORT";
				position[]={2500, 15, 9400};
			};
			class Stolby
			{
				name="STOLBY CRAGS";
				position[]={10100, 120, 1000};
			};
			class Industrial
			{
				name="INDUSTRIAL ZONE";
				position[]={7200, 12, 5200};
			};
		};

		// Навигационная сетка для зомби (см. docs/05). Если navmesh не генерировали —
		// временно оставьте ссылку на navmesh chernarusplus (зомби просто не будут
		// ходить по вашим улицам, пока вы не сгенерируете свой navmesh.nm).
		class Navmesh
		{
			navmeshName = "\Krasnoyarsk\navmesh\navmesh.nm";
			filterIsolatedIslandsOnLoad = true;
			visualiseOffset = 0.0;

			class GenParams
			{
				tileWidth = 50.0;

				cellSize1 = 0.25;
				cellSize2 = 0.1;
				cellSize3 = 0.1;

				filterIsolatedIslands = true;
				seedPosition[] = {6144, 0, 6144};

				class Agent
				{
					diameter = 0.6;

					standHeight = 1.5;
					crouchHeight = 1.0;
					proneHeight = 0.5;

					maxStepHeight = 0.45;
					maxSlope = 60.0;
				};

				class Links
				{
					class ZedJump387_050
					{
						jumpLength = 1.50;
						jumpHeight = 0.50;
						minCenterHeight = 0.3;
						jumpDropdownMin = 0.5;
						jumpDropdownMax = -0.5;
						areaType="jump0";
						flags[] = {"jumpOver"};
						color = 0x66ff0000;
					};
					class ZedJump388_050
					{
						jumpLength = 1.50;
						jumpHeight = 0.50;
						minCenterHeight = -0.5;
						jumpDropdownMin = 0.5;
						jumpDropdownMax = -0.5;
						areaType="jump0";
						flags[] = {"jumpOver"};
						color = 0x66dd5500;
					};
					class ZedJump387_110
					{
						jumpLength = 3.90;
						jumpHeight = 1.1;
						minCenterHeight = 0.5;
						jumpDropdownMin = 0.5;
						jumpDropdownMax = -0.5;
						areaType="jump0";
						flags[] = {"jumpOver"};
						color = 0x66008000;
					};
					class ZedJump420_160
					{
						jumpLength = 4.0;
						jumpHeight = 1.6;
						minCenterHeight = 1.1;
						jumpDropdownMin = 0.5;
						jumpDropdownMax = -0.5;
						areaType="jump0";
						flags[] = {"jumpOver"};
						color = 0x660000ff;
					};
					class ZedJump265_210
					{
						jumpLength = 2.45;
						jumpHeight = 2.5;
						minCenterHeight = 1.8;
						jumpDropdownMin = 0.5;
						jumpDropdownMax = -0.5;
						areaType="jump0";
						flags[] = {"climb"};
						color = 0x669400d3;
					};
					class Fence50_110deer
					{
						typeId = 100;
						jumpLength = 8.0;
						jumpHeight = 1.1;
						minCenterHeight = 0.5;
						jumpDropdownMin = 1.0;
						jumpDropdownMax = -1.0;
						areaType="jump2";
						flags[] = {"jumpOver"};
						color = 0x66aaaaFF;
					};
					class Fence110_160deer
					{
						typeId = 101;
						jumpLength = 8.0;
						jumpHeight = 1.6;
						minCenterHeight = 1.1;
						jumpDropdownMin = 1.0;
						jumpDropdownMax = -1.0;
						areaType="jump3";
						flags[] = {"jumpOver"};
						color = 0x6624fff8;
					};
					class Fence50_110hen
					{
						typeId = 110;
						jumpLength = 4.0;
						jumpHeight = 1.1;
						minCenterHeight = 0.5;
						jumpDropdownMin = 0.5;
						jumpDropdownMax = -0.5;
						areaType="jump4";
						flags[] = {"jumpOver"};
						color = 0xFFFFAA00;
					};
					class Fence110_160hen
					{
						typeId = 111;
						jumpLength = 4.0;
						jumpHeight = 1.6;
						minCenterHeight = 1.1;
						jumpDropdownMin = 0.5;
						jumpDropdownMax = -0.5;
						areaType="jump4";
						flags[] = {"jumpOver"};
						color = 0xFFFFAA00;
					};
				};
			};
		};
	};
};

class CfgWorldList
{
	class Krasnoyarsk
	{
	};
};
