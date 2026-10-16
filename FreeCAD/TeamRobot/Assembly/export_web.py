# -*- coding: utf-8 -*-
"""조립 모델(FCStd)을 웹 조립 시뮬레이션용 메시 데이터로 내보내기 (FreeCAD 1.1.x, GUI 모드 필요: 색상 읽기).

실행:
  TR_SRC=<조립 FCStd> TR_WEB_DATA=<출력 폴더> FREECAD_USER_HOME=<임시> QT_QPA_PLATFORM=offscreen \
    ~/Application/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage export_web.py

출력: <출력 폴더>/assembly.json (부품·인스턴스·체결 부품 목록), assembly.bin (정점/인덱스/모서리 선)
원본 FCStd는 열기만 하고 저장하지 않는다.
"""
import os, json, struct, time, traceback
import FreeCAD as App
import FreeCADGui as Gui
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('TR_SRC', os.path.join(HERE, 'TeamRobot_Base_v5_Assembly.FCStd'))
OUT = os.environ.get('TR_WEB_DATA', os.path.join(HERE, '..', 'web', 'data'))
LOG = os.path.join(OUT, 'export.log')
os.makedirs(OUT, exist_ok=True)
logf = open(LOG, 'w', encoding='utf-8')


def L(*a):
    logf.write(' '.join(str(x) for x in a) + '\n')
    logf.flush()


def hexcolor(c):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(v * 255)))) for v in c[:3])


def face_colors(obj, nfaces):
    """객체의 면별 색 (FreeCAD 1.x ShapeAppearance). 면 수와 맞지 않으면 첫 색으로 통일."""
    vo = obj.ViewObject
    try:
        sa = vo.ShapeAppearance
        cols = [hexcolor(m.DiffuseColor) for m in sa]
    except Exception:
        cols = [hexcolor(vo.ShapeColor)]
    if len(cols) == nfaces:
        return cols
    return [cols[0]] * nfaces


class Bin:
    def __init__(self):
        self.buf = bytearray()

    def add(self, fmt, values):
        while len(self.buf) % 4:
            self.buf.append(0)
        off = len(self.buf)
        self.buf += struct.pack('<%d%s' % (len(values), fmt), *values)
        return off


B = Bin()


def tess_faces(shape, cols, tol):
    """면별 테셀레이션 [(색, 점 리스트, 삼각형 리스트)]"""
    out = []
    for f, col in zip(shape.Faces, cols):
        try:
            pts, tris = f.tessellate(tol)
        except Exception:
            continue
        if tris:
            out.append((col, pts, tris))
    return out


def box_faces(bb, col):
    """바운딩 박스를 6개 면 메시로 (간략화 대체용)"""
    x0, y0, z0, x1, y1, z1 = bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax
    V = App.Vector
    quads = [((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)), ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)),
             ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)), ((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)),
             ((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)), ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))]
    return [(col, [V(*q) for q in quad], [(0, 1, 2), (0, 2, 3)]) for quad in quads]


def edge_lines(shapes, defl):
    seg = []
    for s in shapes:
        for e in s.Edges:
            try:
                pts = e.discretize(Deflection=defl)
            except Exception:
                continue
            for a, b in zip(pts, pts[1:]):
                seg.extend((a.x, a.y, a.z, b.x, b.y, b.z))
    return seg


def write_asset(name, faces, edge_shapes=None, defl=0.05, ref_bb=None):
    """faces: tess_faces 결과를 합친 목록. 좌표는 에셋 범위 기준 16비트 양자화, 인덱스 16비트(청크당 정점 65535 이하)."""
    t = time.time()
    xs = [p.x for _, P, _ in faces for p in P]
    ys = [p.y for _, P, _ in faces for p in P]
    zs = [p.z for _, P, _ in faces for p in P]
    lo = (min(xs), min(ys), min(zs))
    hi = (max(xs), max(ys), max(zs))
    sc = [max(h - l, 1e-6) / 65535.0 for l, h in zip(lo, hi)]
    bycol = {}
    for col, P, T in faces:
        bycol.setdefault(col, []).append((P, T))
    chunks = []
    ntri = 0
    for col, flist in bycol.items():
        Q, I = [], []
        def flush():
            if I:
                chunks.append({'color': col, 'pos': B.add('H', Q), 'nv': len(Q) // 3, 'idx': B.add('H', I), 'ni': len(I)})
        for P, T in flist:
            if len(Q) // 3 + len(P) > 65535:
                flush()
                Q, I = [], []
            base = len(Q) // 3
            for p in P:
                Q.extend((int(round((p.x - lo[0]) / sc[0])), int(round((p.y - lo[1]) / sc[1])), int(round((p.z - lo[2]) / sc[2]))))
            for a, b_, c in T:
                I.extend((a + base, b_ + base, c + base))
            ntri += len(T)
        flush()
    a = {'name': name, 'qmin': [round(v, 5) for v in lo], 'qscale': [v for v in sc], 'chunks': chunks}
    if edge_shapes:
        seg = edge_lines(edge_shapes, defl)
        a['edges'] = {'pos': B.add('f', seg), 'nv': len(seg) // 3}
    a['bbox'] = [round(v, 3) for v in lo + hi]
    msg = f"asset {name}: {len(chunks)} chunks, {ntri} tris, {sum(c['nv'] for c in chunks)} verts, edges {a.get('edges', {}).get('nv', 0) // 2} segs, {time.time() - t:.1f}s"
    if ref_bb is not None:
        dev = max(abs(lo[0] - ref_bb.XMin), abs(lo[1] - ref_bb.YMin), abs(lo[2] - ref_bb.ZMin), abs(hi[0] - ref_bb.XMax), abs(hi[1] - ref_bb.YMax), abs(hi[2] - ref_bb.ZMax))
        msg += f", bbox dev {dev:.3f}"
        if dev > 0.6:
            msg += ' !! 메시 범위가 형상과 다름'
    L(msg)
    return a


def placed(obj, plc):
    s = obj.Shape.copy()
    s.Placement = plc
    return s


def mat(plc):
    m = plc.toMatrix()
    return [m.A11, m.A12, m.A13, m.A14, m.A21, m.A22, m.A23, m.A24, m.A31, m.A32, m.A33, m.A34, m.A41, m.A42, m.A43, m.A44]


def cyl_axes(shape, radius, axis, tol=1e-3):
    out = {}
    for f in shape.Faces:
        su = f.Surface
        if not isinstance(su, Part.Cylinder) or abs(su.Radius - radius) > tol or abs(abs(su.Axis.dot(axis)) - 1) > 1e-6:
            continue
        c = su.Center
        key = (round(c.x, 3), round(c.z, 3)) if abs(axis.y) > 0.5 else (round(c.x, 3), round(c.y, 3))
        out[key] = True
    return sorted(out)


def main():
    L('FreeCAD', '.'.join(App.Version()[:3]), 'src', SRC)
    doc = App.openDocument(SRC)
    Gui.setActiveDocument(doc.Name)
    g = doc.getObject
    X, Y, Z = App.Vector(1, 0, 0), App.Vector(0, 1, 0), App.Vector(0, 0, 1)
    assets, inst = {}, []

    def simple(obj, name, tol=0.05):
        s = obj.Shape.copy()
        assets[name] = write_asset(name, tess_faces(s, face_colors(obj, len(s.Faces)), tol), [s], ref_bb=s.BoundBox)

    # 밑판·기둥판·브라켓·가이드 블록·바퀴: 월드 좌표 그대로
    plate = g('Body')
    simple(plate, 'plate')
    inst.append({'id': 'plate', 'asset': 'plate', 'group': 'plate', 'name': plate.Label})
    for side in ('L', 'R'):
        o = g(f'Pillar_{side}')
        simple(o, f'pillar_{side}')
        inst.append({'id': f'pillar_{side}', 'asset': f'pillar_{side}', 'group': 'pillar', 'name': o.Label})
    for o in doc.Objects:
        if o.TypeId == 'PartDesign::Body' and o.Name.startswith('Bracket_'):
            simple(o, o.Name)
            inst.append({'id': o.Name, 'asset': o.Name, 'group': 'bracket', 'name': o.Label})
        if o.TypeId == 'PartDesign::Body' and o.Name.startswith('GuideBlock_'):
            simple(o, o.Name)
            inst.append({'id': o.Name, 'asset': o.Name, 'group': 'guide', 'name': o.Label})
        if o.TypeId == 'Part::Feature' and o.Name.startswith('Wheel_'):
            simple(o, o.Name, 0.08)
            inst.append({'id': o.Name, 'asset': o.Name, 'group': 'wheel', 'name': o.Label})

    # 개조형 모터: 로컬 좌표 메시 1개 + 인스턴스 4개
    # STEP에 색 정보가 없어(전부 기본 회색) 부품 이름으로 색 지정
    MOTOR_COL = (('DC12_C04_CASE', '#2b2d31'), ('DC12_C04_SEAL', '#141516'), ('WBH_', '#8b9097'), ('HN12_N105', '#c3c7cc'))
    dmod = g('DXL_Modified')
    faces, shapes = [], []
    for lk in dmod.Group:
        if lk.TypeId != 'App::Link':
            continue
        src = lk.LinkedObject
        s = placed(src, lk.Placement)
        col = next((c for k, c in MOTOR_COL if src.Label.startswith(k)), '#5a5e66')
        faces += tess_faces(s, [col] * len(s.Faces), 0.08)
        shapes.append(s)
    assets['motor'] = write_asset('motor', faces, shapes, 0.08, ref_bb=Part.makeCompound(shapes).BoundBox)
    for tag in ('FL', 'FR', 'RL', 'RR'):
        o = g(f'DXL_{tag}')
        inst.append({'id': o.Name, 'asset': 'motor', 'group': 'motor', 'name': o.Label, 'matrix': mat(o.Placement)})

    # Jetson: STEP 루트 기준 로컬 메시 + 인스턴스 1개
    jl = g('Jetson_DevKit')
    jroot = jl.LinkedObject
    feats = []

    def walk(o):
        for c in getattr(o, 'Group', []):
            if c.TypeId == 'Part::Feature' and not c.Shape.isNull() and c.Shape.Faces:
                feats.append(c)
            elif c.TypeId == 'App::Part':
                walk(c)
    walk(jroot)
    # 간략화: 2 mm 미만 부품 제외, 크기 비례 허용 오차, 무거운 상자형 부품은 바운딩 박스로 대체
    KEEP = ('375-0137-000', '600-13768-0000-A04', '095-0180-000-TS1', '3514', 'GROGU_MODULE_BOARD_ME', 'LEAFSPRING')
    faces, edge_src, stats = [], [], {'skip': 0, 'box': [], 'coarse': 0}
    all_bb = []
    for c in feats:
        s = placed(c, c.getGlobalPlacement())
        bb = s.BoundBox
        all_bb.append(bb)
        if bb.DiagonalLength < 2.0:
            stats['skip'] += 1
            continue
        cols = face_colors(c, len(s.Faces))
        tol = max(0.15, 0.004 * bb.DiagonalLength)
        fl = tess_faces(s, cols, tol)
        n = sum(len(t) for _, _, t in fl)
        if n > 6000:
            fl = tess_faces(s, cols, tol * 3)
            n = sum(len(t) for _, _, t in fl)
            stats['coarse'] += 1
            if n > 6000 and not any(c.Label.startswith(k) for k in KEEP):
                main_col = max(set(cols), key=cols.count)
                fl = box_faces(bb, main_col)
                stats['box'].append(c.Label)
        faces += fl
        if c.Label in ('600-13768-0000-A04', '375-0137-000'):
            edge_src.append(s)
    L(f"Jetson features: {len(feats)}, 제외(2mm 미만) {stats['skip']}, 거칠게 {stats['coarse']}, 상자 대체 {len(stats['box'])}: {stats['box']}")
    jbb = App.BoundBox()
    for bb in all_bb:
        jbb.add(bb)
    assets['jetson'] = write_asset('jetson', faces, edge_src, 0.15)
    assets['jetson']['note'] = '웹 표시용 간략화: 2 mm 미만 부품 제외, 일부 커넥터 상자 대체'
    inst.append({'id': 'jetson', 'asset': 'jetson', 'group': 'jetson', 'name': jl.Label, 'matrix': mat(jl.Placement)})

    # 체결 부품: 실제 구멍 위치에서 생성
    ps = plate.Shape
    pb = ps.BoundBox
    fast = []
    for (x, y) in cyl_axes(ps, 1.45, Z):
        fast.append({'kind': 'screw', 'group': 'motor', 'pos': [x, y, pb.ZMin], 'dir': [0, 0, 1], 'd': 2.5, 'len': 8, 'headD': 4.5, 'headH': 2.5,
                     'label': 'M2.5 모터-밑판 (길이 미정, 8 이하)'})
    br = [o for o in doc.Objects if o.Name.startswith('BrLegH_')][0]
    brv = [o for o in doc.Objects if o.Name.startswith('BrLegV_')][0]
    br_top = pb.ZMax + br.Height.Value
    for (x, y) in cyl_axes(ps, 1.7, Z):
        fast.append({'kind': 'screw', 'group': 'bracket', 'pos': [x, y, br_top], 'dir': [0, 0, -1], 'd': 3, 'len': 12, 'headD': 5.5, 'headH': 3,
                     'label': 'M3x12 브라켓-밑판 (가정)'})
        fast.append({'kind': 'nut', 'group': 'bracket', 'pos': [x, y, pb.ZMin], 'dir': [0, 0, -1], 'af': 5.5, 't': 2.4, 'label': 'M3 너트 (가정)'})
    for side, sy in (('L', 1), ('R', -1)):
        s = g(f'Pillar_{side}').Shape
        bb = s.BoundBox
        y_in = bb.YMin if sy > 0 else bb.YMax
        y_out = bb.YMax if sy > 0 else bb.YMin
        for (x, z) in cyl_axes(s, 1.45, Y):
            fast.append({'kind': 'screw', 'group': 'pillar', 'pos': [x, y_in, z], 'dir': [0, sy, 0], 'd': 2.5, 'len': 35, 'headD': 4.5, 'headH': 2.5,
                         'label': 'M2.5x35~37 기둥판-모터 (케이스 조립 볼트 교체, 미정)'})
        for (x, z) in cyl_axes(s, 1.7, Y):
            yb = y_out + sy * brv.Width.Value
            fast.append({'kind': 'screw', 'group': 'bracket', 'pos': [x, yb, z], 'dir': [0, -sy, 0], 'd': 3, 'len': 12, 'headD': 5.5, 'headH': 3,
                         'label': 'M3x12 브라켓-기둥판 (가정)'})
            fast.append({'kind': 'nut', 'group': 'bracket', 'pos': [x, y_in, z], 'dir': [0, -sy, 0], 'af': 5.5, 't': 2.4, 'label': 'M3 너트 (가정)'})
    L('fasteners', {k: sum(1 for f in fast if f['group'] == k and f['kind'] == 'screw') for k in ('motor', 'pillar', 'bracket')},
      'nuts', sum(1 for f in fast if f['kind'] == 'nut'))

    ground_z = [o for o in doc.Objects if o.Name == 'Ground'][0].Placement.Base.z
    with open(os.path.join(OUT, 'assembly.bin'), 'wb') as fbin:
        fbin.write(B.buf)
    man = {'source': os.path.basename(SRC), 'units': 'mm', 'up': 'Z', 'groundZ': ground_z, 'assets': assets, 'instances': inst, 'fasteners': fast,
           'bin': 'assembly.bin', 'binBytes': len(B.buf)}
    with open(os.path.join(OUT, 'assembly.json'), 'w', encoding='utf-8') as fj:
        json.dump(man, fj, ensure_ascii=False, separators=(',', ':'))
    L(f"bin {len(B.buf) / 1e6:.2f} MB, json {os.path.getsize(os.path.join(OUT, 'assembly.json')) / 1e3:.1f} kB")
    App.closeDocument(doc.Name)
    L('done')


try:
    main()
except Exception:
    L(traceback.format_exc())
finally:
    logf.close()
    os._exit(0)
