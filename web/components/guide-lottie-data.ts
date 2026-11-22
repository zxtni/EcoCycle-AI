// Original vector artwork. All points are on the same 96 × 96 Lottie canvas.
export type GuideScene = "welcome" | "account" | "scan" | "loading" | "review" | "saved" | "nearby" | "impact";

type Point = [number, number];
const lime = [0.84, 0.97, 0.57, 1];
const light = [0.97, 0.99, 0.92, 1];
const dark = [0.17, 0.32, 0.21, 1];
const steady = <T>(k: T) => ({a: 0, k});
const ease = {i: {x: [0.55], y: [1]}, o: {x: [0.25], y: [0]}};
const animated = (frames: [number, number[]][]) => ({
  a: 1,
  k: frames.map(([t, s], index) => index === frames.length - 1 ? {t, s} : {t, s, ...ease}),
});

function path(points: Point[], closed = false) {
  const tangents = points.map(() => [0, 0]);
  return {ty: "sh", ks: steady({v: points, i: tangents, o: tangents, c: closed})};
}
function circle(center: Point, diameter: number) {
  return {ty: "el", p: steady(center), s: steady([diameter, diameter]), d: 1};
}
function stroke(color: number[], width: number) {
  return {ty: "st", c: steady(color), o: steady(100), w: steady(width), lc: 2, lj: 2};
}
function fill(color: number[]) {
  return {ty: "fl", c: steady(color), o: steady(100), r: 1};
}

const corners = [
  path([[-23,-12],[-23,-23],[-12,-23]]), path([[12,-23],[23,-23],[23,-12]]),
  path([[23,12],[23,23],[12,23]]), path([[-12,23],[-23,23],[-23,12]]),
];
const artwork = {
  welcome: [circle([0,-11],17), path([[-20,21],[-17,12],[-8,7],[8,7],[17,12],[20,21]])],
  account: [circle([-6,-10],16), path([[-24,20],[-21,11],[-13,6],[1,6],[9,12],[12,20]]),
    path([[18,-14],[18,0]]), path([[11,-7],[25,-7]])],
  scan: [...corners, circle([0,0],16)],
  loading: [...corners],
  review: [path([[-18,-22],[11,-22],[19,-14],[19,22],[-18,22]],true),
    path([[-10,-7],[10,-7]]), path([[-10,3],[10,3]]), path([[-10,13],[3,13]])],
  saved: [circle([0,0],46), path([[-11,0],[-3,9],[13,-10]])],
  nearby: [path([[0,25],[-15,7],[-19,-4],[-15,-16],[-7,-22],[7,-22],[15,-16],[19,-4],[15,7]],true),circle([0,-5],11)],
  impact: [path([[-20,17],[-20,8]]), path([[-7,17],[-7,0]]), path([[6,17],[6,-8]]),
    path([[19,17],[19,-16]]), path([[-20,-1],[-5,-9],[7,-15],[17,-23]])],
};

function layer(index: number, name: string, shapes: object[], motion: object = {}, frames = 60) {
  return {ddd: 0, ind: index, ty: 4, nm: name, sr: 1, ip: 0, op: frames, st: 0, bm: 0,
    ks: {o: steady(100), r: steady(0), a: steady([0,0,0]), p: steady([48,48,0]), s: steady([100,100,100]), ...motion},
    shapes};
}

export function guideAnimation(scene: GuideScene, onDark: boolean) {
  const ink = onDark ? light : dark;
  const icon = layer(2,"Guide icon",[...artwork[scene],stroke(ink,3.2)],{
    s: animated([[0,[82,82,100]],[19,[106,106,100]],[32,[100,100,100]]]),
  });
  const accent = scene === "loading"
    ? layer(1,"Scanning sweep",[path([[-19,0],[19,0]]),stroke(onDark ? lime : dark,3.5)],{
      p: animated([[0,[48,34,0]],[27,[48,62,0]],[59,[48,34,0]]]),
    })
    : layer(1,"Completion accents",[circle([28,-26],6),circle([-29,21],5),circle([27,24],4),fill(onDark ? lime : dark)],{
      o: animated([[0,[0]],[17,[78]],[49,[28]],[59,[0]]]),
      s: animated([[0,[60,60,100]],[27,[100,100,100]]]),
    });
  return {v:"5.12.2",fr:30,ip:0,op:60,w:96,h:96,nm:scene,ddd:0,assets:[],layers:[accent,icon]};
}
