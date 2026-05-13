export type IssueType =
  | 'snow'
  | 'pothole'
  | 'road_obstruction'
  | 'flooding'
  | 'broken_streetlight'
  | 'broken_sidewalk'
  | 'water_leak'
  | 'sewer_overflow'
  | 'illegal_dumping'
  | 'other';

export const ISSUE_TYPE_LABELS: Record<IssueType, string> = {
  snow: 'Снег',
  pothole: 'Яма',
  road_obstruction: 'Препятствие на дороге',
  flooding: 'Подтопление',
  broken_streetlight: 'Неисправное освещение',
  broken_sidewalk: 'Сломанный тротуар',
  water_leak: 'Утечка воды',
  sewer_overflow: 'Проблема с канализацией',
  illegal_dumping: 'Незаконная свалка',
  other: 'Другое'
};