# priorityclip-geo

Инструмент детерминированно распределяет перекрывающиеся территории между
полигонами. Объект с меньшим числовым приоритетом получает общую площадь первым.

```bash
priorityclip partition areas.gpkg --priority priority \
  --output partitioned.gpkg --report areas.csv
```

Объединённая территория сохраняется, итоговые полигоны не перекрываются, а CSV
показывает исходную, итоговую и удалённую площадь каждого объекта.

Copyright 2026 Alena Nikitina. Apache License 2.0.

