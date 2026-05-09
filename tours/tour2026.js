// Tour de France 2026 – Tour-Plugin für VeloPathMapper
// Registriert sich in window.VPM_TOURS
(function () {
  const TIMES = {
    1:  { start:'15:30', finish:'17:15', itt:true,  points:[] },
    2:  { start:'13:00', finish:'17:20', itt:false, points:[] },
    3:  { start:'12:00', finish:'17:10', itt:false, points:[] },
    4:  { start:'13:15', finish:'17:25', itt:false, points:[] },
    5:  { start:'13:00', finish:'16:45', itt:false, points:[] },
    6:  { start:'12:15', finish:'17:05', itt:false, points:[] },
    7:  { start:'13:00', finish:'16:50', itt:false, points:[] },
    8:  { start:'13:15', finish:'17:00', itt:false, points:[] },
    9:  { start:'12:45', finish:'17:15', itt:false, points:[] },
    10: { start:'12:30', finish:'17:00', itt:false, points:[] },
    11: { start:'13:15', finish:'16:40', itt:false, points:[] },
    12: { start:'13:30', finish:'17:00', itt:false, points:[] },
    13: { start:'11:45', finish:'17:10', itt:false, points:[] },
    14: { start:'12:30', finish:'17:05', itt:false, points:[] },
    15: { start:'12:15', finish:'17:00', itt:false, points:[] },
    16: { start:'14:00', finish:'17:00', itt:true,  points:[] },
    17: { start:'13:30', finish:'16:55', itt:false, points:[] },
    18: { start:'12:45', finish:'17:10', itt:false, points:[] },
    19: { start:'13:00', finish:'16:45', itt:false, points:[] },
    20: { start:'11:30', finish:'17:00', itt:false, points:[] },
    21: { start:'17:00', finish:'19:30', itt:false, points:[] },
  };

  const STAGES = [
    {n:1,  date:'Sa 4. Juli',  start:'Barcelona',           finish:'Barcelona',           dist:19,  elev:50,   type:'itt',     sll:[41.385,2.173],  fll:[41.385,2.173],  slug:'barcelona-barcelona',      climbs:'Mannschaftszeitfahren (TTT) · 19 km · Teamzeit auf erstem Fahrer, Einzelzeiten für GC'},
    {n:2,  date:'So 5. Juli',  start:'Tarragona',            finish:'Barcelona',           dist:182, elev:2400, type:'hilly',   sll:[41.118,1.244],  fll:[41.385,2.173],  slug:'tarragona-barcelona',      climbs:'Über Montjuïc · hügeliges Finale in Barcelona'},
    {n:3,  date:'Mo 6. Juli',  start:'Granollers',           finish:'Les Angles',          dist:196, elev:4000, type:'mountain',sll:[41.608,2.288],  fll:[42.578,2.073],  slug:'granollers-les-angles',    climbs:'Erste Pyrenäen-Etappe · ca. 4.000 Hm · Bergziel Les Angles'},
    {n:4,  date:'Di 7. Juli',  start:'Carcassonne',          finish:'Foix',                dist:182, elev:2800, type:'hilly',   sll:[43.213,2.351],  fll:[42.965,1.607],  slug:'carcassonne-foix',         climbs:'Pyrenäen-Vorland · welliges Terrain'},
    {n:5,  date:'Mi 8. Juli',  start:'Lannemezan',           finish:'Pau',                 dist:158, elev:600,  type:'sprint',  sll:[43.125,0.386],  fll:[43.295,-0.368], slug:'lannemezan-pau',           climbs:'Flachetappe · erste Sprintchance für die Sprinter'},
    {n:6,  date:'Do 9. Juli',  start:'Pau',                  finish:'Gavarnie-Gèdre',      dist:186, elev:4150, type:'mountain',sll:[43.295,-0.368], fll:[42.955,-0.009], slug:'pau-gavarnie-gedre',       climbs:"Col d'Aspin · Col du Tourmalet · Ziel am UNESCO-Cirque de Gavarnie · spektakuläre Bergankunft"},
    {n:7,  date:'Fr 10. Juli', start:'Hagetmau',             finish:'Bordeaux',            dist:175, elev:400,  type:'sprint',  sll:[43.658,-0.319], fll:[44.837,-0.579], slug:'hagetmau-bordeaux',        climbs:'Flachetappe durch die Landes · Sprint-Finale in Bordeaux'},
    {n:8,  date:'Sa 11. Juli', start:'Périgueux',            finish:'Bergerac',            dist:182, elev:400,  type:'sprint',  sll:[45.184,0.721],  fll:[44.853,0.483],  slug:'perigueux-bergerac',       climbs:'Flachetappe durch die Dordogne · erneute Sprintchance'},
    {n:9,  date:'So 12. Juli', start:'Malemort',             finish:'Ussel',               dist:185, elev:3500, type:'hilly',   sll:[45.170,1.564],  fll:[45.550,2.309],  slug:'malemort-ussel',           climbs:'Hügelige Etappe durch das Limousin · ca. 3.500 Hm · Ausreißerfreundlich'},
    {n:10, date:'Di 14. Juli', start:'Aurillac',             finish:'Le Lioran',           dist:167, elev:3900, type:'mountain',sll:[44.926,2.439],  fll:[45.089,2.741],  slug:'aurillac-le-lioran',       climbs:'Bastille-Tag · Zentralmassiv · Auvergne-Vulkane · Bergziel Le Lioran'},
    {n:11, date:'Mi 15. Juli', start:'Vichy',                finish:'Nevers',              dist:161, elev:1800, type:'sprint',  sll:[46.131,3.427],  fll:[46.990,3.157],  slug:'vichy-nevers',             climbs:'Flachetappe mit welligem Terrain · Sprint-Finale in Nevers'},
    {n:12, date:'Do 16. Juli', start:'Nevers Magny-Cours',   finish:'Chalon-sur-Saône',    dist:181, elev:500,  type:'sprint',  sll:[46.864,3.151],  fll:[46.781,4.853],  slug:'magny-cours-chalon-sur-saone', climbs:'Start am ehemaligen F1-Circuit de Nevers Magny-Cours · flache Etappe'},
    {n:13, date:'Fr 17. Juli', start:'Dole',                 finish:'Belfort',             dist:205, elev:2200, type:'hilly',   sll:[47.092,5.489],  fll:[47.640,6.864],  slug:'dole-belfort',             climbs:'Längste Etappe der Tour 2026 · welliges Jura-Gebiet · ideal für Ausreißer'},
    {n:14, date:'Sa 18. Juli', start:'Mulhouse',             finish:'Le Markstein',        dist:155, elev:3800, type:'mountain',sll:[47.750,7.336],  fll:[47.926,7.009],  slug:'mulhouse-le-markstein',    climbs:'Vogesen · Col du Haag · Grand Ballon · Bergziel Le Markstein'},
    {n:15, date:'So 19. Juli', start:'Champagnole',          finish:'Plateau de Solaison', dist:184, elev:4700, type:'mountain',sll:[46.748,5.907],  fll:[46.150,6.333],  slug:'champagnole-plateau-de-solaison', climbs:'Bergziel Plateau de Solaison: 11,3 km bei Ø 9,1 % · anspruchsvolle Alpen-Etappe'},
    {n:16, date:'Di 21. Juli', start:'Évian-les-Bains',      finish:'Thonon-les-Bains',    dist:26,  elev:500,  type:'itt',     sll:[46.401,6.590],  fll:[46.371,6.479],  slug:'evian-thonon',             climbs:'Einzelzeitfahren · 26 km · hartes bergiges Profil mit Côte de Larringes · wichtig für das GC'},
    {n:17, date:'Mi 22. Juli', start:'Chambéry',             finish:'Voiron',              dist:175, elev:2400, type:'sprint',  sll:[45.564,5.918],  fll:[45.364,5.590],  slug:'chambery-voiron',          climbs:'Letzte Sprintchance vor den Alpen · Col des Prés (1.100 m) · Col de Couz · finale Wellen'},
    {n:18, date:'Do 23. Juli', start:'Voiron',               finish:'Orcières-Merlette',   dist:185, elev:3800, type:'mountain',sll:[45.364,5.590],  fll:[44.689,6.325],  slug:'voiron-orcieres-merlette', climbs:'Südliche Alpen · Bergziel Orcières-Merlette · Anstieg abseits der Hauptrouten'},
    {n:19, date:'Fr 24. Juli', start:'Gap',                  finish:"Alpe d'Huez",         dist:128, elev:3200, type:'mountain',sll:[44.556,6.079],  fll:[45.093,6.071],  slug:'gap-alpe-dhuez',           climbs:"Klassische 21 Kehren von Alpe d'Huez · erste Bergankunft auf dem legendären Anstieg seit 2022"},
    {n:20, date:'Sa 25. Juli', start:"Le Bourg-d'Oisans",    finish:"Alpe d'Huez",         dist:171, elev:5600, type:'mountain',sll:[45.053,6.030],  fll:[45.093,6.071],  slug:'le-bourg-doisans-alpe-dhuez', climbs:"Königsetappe · Col de la Croix de Fer · Télégraphe · Galibier (2.642 m) · Col de Sarenne · Alpe d'Huez · ca. 5.600 Hm"},
    {n:21, date:'So 26. Juli', start:'Thoiry',               finish:'Paris',               dist:130, elev:900,  type:'sprint',  sll:[48.867,1.800],  fll:[48.856,2.352],  slug:'thoiry-paris',             climbs:'Abschlussetappe · 3 Überfahrten von Montmartre (Sacré-Cœur) · Zielsprint auf den Champs-Élysées'},
  ];

  const REST = [
    {before:10, date:'Mo 13. Juli', label:'Ruhetag 1 – Cantal (Zentralmassiv)'},
    {before:16, date:'Mo 20. Juli', label:'Ruhetag 2 – Haute-Savoie (Alpen)'},
  ];

  window.VPM_TOURS = window.VPM_TOURS || [];
  window.VPM_TOURS.push({
    id:          'tour2026',
    name:        'Tour de France 2026',
    shortName:   'Tour 2026',
    emoji:       '🏆',
    color:       '#f59e0b',
    textColor:   '#1a1a2e',
    edition:     '113. Ausgabe',
    dates:       '4.–26. Juli 2026',
    startDesc:   'Grand Départ: Barcelona',
    totalDist:   '~3.333 km',
    totalElev:   '~51.200 Hm',
    mapCenter:   [46, 3],
    mapZoom:     6,
    gpxBase:     'gpx/tour2026/',
    profileBase: 'profile/tour2026/',
    urls: {
      official: (n, _slug) => `https://www.letour.fr/de/stage/${n}`,
      pcs:      n           => `https://www.procyclingstats.com/race/tour-de-france/2026/stage-${n}`,
      cs:       n           => `https://www.cyclingstage.com/tour-de-france-2026-route/stage-${n}-france-2026/`,
    },
    times:  TIMES,
    stages: STAGES,
    rest:   REST,
  });
}());
