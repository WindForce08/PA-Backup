# -*- coding: utf-8 -*-
"""TeamRobot 밑판 v3 조립 모델 생성 스크립트 (FreeCAD 1.1.x, GUI 모드 필요).

v2 대비 변경:
  - 모터 배치는 후보 B(세움)로 확정하고 상하 반전 (출력축 쪽 끝면이 밑판에 닿음)
  - Ø65 일반 바퀴 4개 (폭·허브는 미확정 -> 자리표시 형상)
  - Jetson은 하부 프레임째로 밑판에 올림 (PCB 장착구멍 참조 제거, 프레임 접지 윤곽 표시)
  - XM430 대신 XW430 STEP을 대용으로 사용 (사용자 허용)

실행 (GUI 창 없이):
  FREECAD_USER_HOME=<임시폴더> QT_QPA_PLATFORM=offscreen \
    ~/Application/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage build_base_v3.py

원본(TeamRobot_Base.FCStd, STEP 파일)은 읽기만 하고 저장하지 않는다.
"""
import os, time, traceback
from collections import Counter
import FreeCAD as App
import FreeCADGui as Gui
import Part
import ImportGui

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_BASE = os.path.join(HERE, '..', 'CAD', 'TeamRobot_Base.FCStd')
DXL_STEP = '/home/pa31/Downloads/XW430.N105.I105.STP'
JET_STEP = '/home/pa31/Downloads/Jetson_Orin_Nano_DevKit_3D_STEP_Model/P3766-P3768SKU4-P3767ENVELOPE.stp'
OUT = os.path.join(HERE, 'TeamRobot_Base_v3_Assembly.FCStd')
LOG = os.path.join(HERE, 'build_base_v3.log')

PROTECTED = {os.path.realpath(p) for p in (SRC_BASE, DXL_STEP, JET_STEP,
                                           os.path.join(HERE, 'TeamRobot_Base_v2_Assembly.FCStd'))}

# ---- 설계 파라미터 ----
SHAFT_X = 100.0          # 구동축 X 위치 (±), v2와 동일 (미확정)
WHEEL_D = 65.0           # 바퀴 지름 (사용자 지정)
WHEEL_W = 20.0           # 바퀴 폭 (가정)
WHEEL_GAP = 3.0          # 바퀴 안쪽 면과 밑판 측면 사이 간격 (가정) -> 모터를 이만큼 바깥으로 이동
HUB_RECESS_D, HUB_RECESS_T = 6.0, 3.0   # 혼 중심 볼트 머리 회피용 홈 (자리표시)
MOTOR_MARGIN = 2.0
JET_MARGIN = 5.0
JET_AIR_TOP = 15.0       # 가정
JET_PORT_ACCESS = 30.0   # 가정
PILLAR_Y_IN, PILLAR_Y_OUT, PILLAR_H = 73.5, 78.5, 90.0  # CartRidar 측벽 치수를 90° 회전해 적용 (미확정)

logf = open(LOG, 'w', encoding='utf-8')


def L(*a):
    msg = ' '.join(str(x) for x in a)
    print(msg)
    logf.write(msg + '\n')
    logf.flush()


def fbb(b):
    return (f"X[{b.XMin:.2f},{b.XMax:.2f}] Y[{b.YMin:.2f},{b.YMax:.2f}] Z[{b.ZMin:.2f},{b.ZMax:.2f}] "
            f"size=({b.XLength:.2f} x {b.YLength:.2f} x {b.ZLength:.2f})")


def fplc(p):
    y, pi, r = p.Rotation.toEuler()
    return f"Pos=({p.Base.x:.2f},{p.Base.y:.2f},{p.Base.z:.2f}) YPR=({y:.1f},{pi:.1f},{r:.1f})"


def rot_from_axes(xm, ym, zm):
    assert abs(xm.cross(ym).sub(zm).Length) < 1e-9, 'not right-handed'
    m = App.Matrix(xm.x, ym.x, zm.x, 0, xm.y, ym.y, zm.y, 0, xm.z, ym.z, zm.z, 0, 0, 0, 0, 1)
    return App.Rotation(m)


def shape_of(o):
    return Part.getShape(o, '', needSubElement=False, transform=True)


def overlap_volume(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    bs = [s for s in b.Solids if s.BoundBox.intersect(a.BoundBox)]
    tot = 0.0
    for sa in a.Solids:
        if not sa.BoundBox.intersect(b.BoundBox):
            continue
        for sb in bs:
            if sa.BoundBox.intersect(sb.BoundBox):
                tot += sa.common(sb).Volume
    return tot


def bbox_gap(a, b):
    dx = max(0, max(a.XMin, b.XMin) - min(a.XMax, b.XMax))
    dy = max(0, max(a.YMin, b.YMin) - min(a.YMax, b.YMax))
    dz = max(0, max(a.ZMin, b.ZMin) - min(a.ZMax, b.ZMax))
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def min_dist(a, b, near=20.0):
    """솔리드 단위 최소 거리. 바운딩 박스 간격이 near 이상이면 그 값(하한)만 반환.
    컴파운드 전체에 distToShape를 쓰면 동축 원통 등에서 메모리가 폭증할 수 있다."""
    g = bbox_gap(a.BoundBox, b.BoundBox)
    if g >= near:
        return g, 'bbox'
    best = None
    for sa in a.Solids:
        for sb in b.Solids:
            if bbox_gap(sa.BoundBox, sb.BoundBox) >= near:
                continue
            d = sa.distToShape(sb)[0]
            best = d if best is None else min(best, d)
            if best == 0.0:
                return 0.0, 'exact'
    return (g, 'bbox') if best is None else (best, 'exact')


def import_step(doc, path):
    App.ParamGet('User parameter:BaseApp/Preferences/Mod/Import/hSTEP').SetBool('ReadShowDialogImport', False)
    pi = App.ParamGet('User parameter:BaseApp/Preferences/Mod/Import')
    pi.SetInt('ImportMode', 0)
    pi.SetBool('UseLinkGroup', False)
    before = set(o.Name for o in doc.Objects)
    t = time.time()
    ImportGui.insert(path, doc.Name)
    new = [o for o in doc.Objects if o.Name not in before]
    roots = [o for o in new if o.TypeId == 'App::Part' and not [p for p in o.InList if p in new]]
    L(f"  import {os.path.basename(path)}: {time.time() - t:.1f}s, 새 객체 {len(new)}개, 루트 {[r.Label for r in roots]}")
    L(f"    객체 유형: {dict(Counter(o.TypeId for o in new))}")
    assert len(roots) == 1, 'STEP 루트 App::Part가 1개가 아님'
    return roots[0], new


def box(doc, name, label, b, group, color, transp=80):
    o = doc.addObject('Part::Box', name)
    o.Label = label
    o.Length, o.Width, o.Height = b.XLength, b.YLength, b.ZLength
    o.Placement = App.Placement(App.Vector(b.XMin, b.YMin, b.ZMin), App.Rotation())
    group.addObject(o)
    o.ViewObject.ShapeColor = color
    o.ViewObject.Transparency = transp
    return o


def grow(b, dx, dy, dz_top, zmin=None):
    return App.BoundBox(b.XMin - dx, b.YMin - dy, b.ZMin if zmin is None else zmin,
                        b.XMax + dx, b.YMax + dy, b.ZMax + dz_top)


def feature(doc, name, label, shape, group, color, transp=0):
    o = doc.addObject('Part::Feature', name)
    o.Label = label
    o.Shape = shape
    group.addObject(o)
    o.ViewObject.ShapeColor = color
    o.ViewObject.Transparency = transp
    return o


def main():
    L('=== TeamRobot 밑판 v3 생성 ===')
    L('FreeCAD', '.'.join(App.Version()[:3]), App.Version()[3])
    L('시각', time.strftime('%Y-%m-%d %H:%M:%S'))
    if os.path.realpath(OUT) in PROTECTED:
        raise RuntimeError('출력 경로가 보호 대상 파일과 같음')
    L('\n[0] 입력 파일')
    for p in (SRC_BASE, DXL_STEP, JET_STEP):
        if not os.path.isfile(p):
            raise FileNotFoundError(p)
        L(f"  OK {os.path.realpath(p)} ({os.path.getsize(p)} bytes, 수정 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p)))})")

    doc = App.newDocument('TeamRobot_Base_v3')
    doc.Label = 'TeamRobot_Base_v3_Assembly'

    # ---- 1. 기존 밑판 복사 ----
    L('\n[1] 기존 밑판 복사')
    src = App.openDocument(os.path.realpath(SRC_BASE))
    body_src = src.getObject('Body')
    ref_vol, ref_bb = body_src.Shape.Volume, body_src.Shape.BoundBox
    L(f"  원본 Body 구성: {[o.Name for o in body_src.Group]}")
    plate = doc.copyObject(body_src, True)
    App.closeDocument(src.Name)
    App.setActiveDocument(doc.Name)
    Gui.setActiveDocument(doc.Name)
    plate.Label = '밑판_270x250x5 (TeamRobot_Base 복사)'
    doc.recompute()
    ps = plate.Shape
    L(f"  원본 Body: vol={ref_vol:.1f} {fbb(ref_bb)}")
    L(f"  복사본   : vol={ps.Volume:.1f} {fbb(ps.BoundBox)} valid={ps.isValid()}")
    assert abs(ps.Volume - ref_vol) < 1e-6, '복사 후 밑판 부피 불일치'
    pb = ps.BoundBox
    PLATE_TOP = pb.ZMax
    plate.ViewObject.ShapeColor = (0.55, 0.62, 0.70)

    # ---- 2. STEP 원본 ----
    L('\n[2] STEP 가져오기 (원본 형상은 수정하지 않고 링크로만 배치)')
    g_src = doc.addObject('App::DocumentObjectGroup', 'STEP_Originals')
    g_src.Label = 'STEP_원본_수정금지(숨김)'
    dxl_root, dxl_new = import_step(doc, DXL_STEP)
    jet_root, jet_new = import_step(doc, JET_STEP)
    g_src.addObject(dxl_root)
    g_src.addObject(jet_root)
    dxl_root.ViewObject.Visibility = False
    jet_root.ViewObject.Visibility = False

    case = [shape_of(o) for o in dxl_new if o.TypeId == 'Part::Feature' and o.Label.startswith('DC12_C04_CASE')]
    case_bb = Part.makeCompound(case).BoundBox
    HORN_Z = [shape_of(o) for o in dxl_new if o.Label == 'HN12_N105_DUMMY'][0].BoundBox.ZMax
    dxl_s = shape_of(dxl_root)
    L(f"  DXL(XW430, XM430 대용) 전체: solids={len(dxl_s.Solids)} valid={dxl_s.isValid()} {fbb(dxl_s.BoundBox)}")
    L(f"  DXL 케이스: {fbb(case_bb)}  혼 바깥면 로컬 Z={HORN_Z:.2f}")
    jet_s = shape_of(jet_root)
    jbb = jet_s.BoundBox
    L(f"  Jetson 전체: solids={len(jet_s.Solids)} {fbb(jbb)}")
    inval = [o.Label for o in dxl_new + jet_new if o.TypeId == 'Part::Feature' and not o.Shape.isNull() and not o.Shape.isValid()]
    L(f"  형상 유효성 실패 객체: {len(inval)} {inval[:10]}")

    # ---- 3. 모터: 후보 B(세움) + 상하 반전 ----
    # 반전 = 출력축 둘레 180° 회전. 혼은 계속 바깥쪽, 로컬 +Y 끝면(축에서 11.25)이 밑판에 닿는다.
    X, Y, Z = App.Vector(1, 0, 0), App.Vector(0, 1, 0), App.Vector(0, 0, 1)
    shaft_y = pb.YMax + WHEEL_GAP - HORN_Z
    shaft_z = PLATE_TOP + case_bb.YMax
    ground_z = shaft_z - WHEEL_D / 2
    g_m = doc.addObject('App::DocumentObjectGroup', 'Motors')
    g_m.Label = '모터_세움_상하반전(XW430 STEP, XM430 대용)'
    g_w = doc.addObject('App::DocumentObjectGroup', 'Wheels')
    g_w.Label = f'바퀴_Ø{WHEEL_D:.0f}_일반(폭 {WHEEL_W:.0f} 가정)'
    motors, wheels = [], []
    for tag, sx, sy in [('FL', +1, +1), ('FR', +1, -1), ('RL', -1, +1), ('RR', -1, -1)]:
        zm = Y * sy
        ym = Z * -1
        xm = ym.cross(zm)
        plc = App.Placement(App.Vector(sx * SHAFT_X, sy * shaft_y, shaft_z), rot_from_axes(xm, ym, zm))
        lk = doc.addObject('App::Link', f'DXL_{tag}')
        lk.LinkedObject = dxl_root
        lk.Placement = plc
        lk.Label = f'DXL_{tag}'
        g_m.addObject(lk)
        ax = doc.addObject('Part::Line', f'Axis_{tag}')
        p0, p1 = plc.multVec(App.Vector(0, 0, case_bb.ZMin)), plc.multVec(App.Vector(0, 0, HORN_Z + WHEEL_W + 15))
        ax.X1, ax.Y1, ax.Z1, ax.X2, ax.Y2, ax.Z2 = p0.x, p0.y, p0.z, p1.x, p1.y, p1.z
        ax.Label = f'구동축_{tag}'
        g_m.addObject(ax)
        ax.ViewObject.LineColor = (0.9, 0.1, 0.1)
        ax.ViewObject.LineWidth = 3
        # 바퀴 자리표시: 혼 바깥면에서 시작, 중심 볼트 머리용 홈
        w = Part.makeCylinder(WHEEL_D / 2, WHEEL_W, App.Vector(0, 0, HORN_Z))
        w = w.cut(Part.makeCylinder(HUB_RECESS_D / 2, HUB_RECESS_T, App.Vector(0, 0, HORN_Z)))
        w.Placement = plc
        wf = feature(doc, f'Wheel_{tag}', f'바퀴_{tag}(Ø{WHEEL_D:.0f}x{WHEEL_W:.0f}, 허브 미확정)', w, g_w, (0.15, 0.15, 0.15))
        motors.append((tag, lk, plc))
        wheels.append((tag, wf))

    # ---- 4. Jetson: 하부 프레임째로 밑판 위 (v2와 같은 위치) ----
    g_j = doc.addObject('App::DocumentObjectGroup', 'JetsonGroup')
    g_j.Label = 'Jetson_OrinNano(하부 프레임째 고정)'
    jplc = App.Placement(App.Vector(pb.XMin + JET_PORT_ACCESS - jbb.YMin, (jbb.XMin + jbb.XMax) / 2.0, PLATE_TOP - jbb.ZMin),
                         App.Rotation(Z, -90))
    jl = doc.addObject('App::Link', 'Jetson_DevKit')
    jl.LinkedObject = jet_root
    jl.Placement = jplc
    jl.Label = 'Jetson_OrinNano_DevKit'
    g_j.addObject(jl)

    doc.recompute()
    jw = shape_of(jl)
    jwb = jw.BoundBox
    zone_j = box(doc, 'Zone_Jetson', 'Jetson_배치공간(측면+5, 상부+15 가정)',
                 grow(jwb, JET_MARGIN, JET_MARGIN, JET_AIR_TOP, zmin=PLATE_TOP), g_j, (0.2, 0.75, 0.3))
    zone_p = box(doc, 'Zone_JetsonPorts', f'Jetson_IO커넥터_접근공간({JET_PORT_ACCESS:.0f}mm 가정)',
                 App.BoundBox(pb.XMin, jwb.YMin, PLATE_TOP, jwb.XMin, jwb.YMax, jwb.ZMax), g_j, (0.95, 0.85, 0.2))
    # 하부 프레임(375-0137) 바닥 접촉 윤곽: STEP 형상을 밑판 상면 바로 위에서 잘라 만든 면
    frame_obj = [o for o in jet_new if o.Label == '375-0137-000'][0]
    fs = shape_of(frame_obj).copy()
    fs.transformShape(jplc.toMatrix())
    sec = fs.slice(Z, PLATE_TOP + 0.3)
    foot = Part.makeFace(sec, 'Part::FaceMakerBullseye')
    foot.translate(App.Vector(0, 0, -0.3 + 0.01))
    fo = feature(doc, 'JetsonFrameFootprint', 'Jetson_하부프레임_접촉윤곽(STEP, 체결구멍 없음)', foot, g_j, (0.85, 0.1, 0.6))
    L(f"\n[4] Jetson 하부 프레임 접촉 윤곽: wire {len(sec)}개, 면적 {foot.Area:.1f} mm², {fbb(foot.BoundBox)}")
    for w_ in sorted(sec, key=lambda w_: -w_.BoundBox.DiagonalLength):
        L(f"    wire {w_.BoundBox.XLength:.2f} x {w_.BoundBox.YLength:.2f} center=({w_.BoundBox.Center.x:.2f},{w_.BoundBox.Center.y:.2f})")

    for tag, lk, plc in motors:
        mb = shape_of(lk).BoundBox
        box(doc, f'Zone_{tag}', f'모터장착공간_{tag}(+{MOTOR_MARGIN:.0f}mm)',
            grow(mb, MOTOR_MARGIN, MOTOR_MARGIN, MOTOR_MARGIN, zmin=PLATE_TOP), g_m, (1.0, 0.55, 0.1))
        k = 0
        for xv in (-8.75, 8.75):
            for zv in (-6, 6):
                w = plc.multVec(App.Vector(xv, case_bb.YMax, zv))
                assert abs(w.z - PLATE_TOP) < 1e-6
                cy = doc.addObject('Part::Cylinder', f'HoleRef_{tag}_{k}')
                cy.Radius, cy.Height = 2.05 / 2, PLATE_TOP - pb.ZMin
                cy.Placement = App.Placement(App.Vector(w.x, w.y, pb.ZMin), App.Rotation())
                cy.Label = f'모터체결구멍_참조_{tag}_{k}(Ø2.05 STEP, 미가공)'
                g_m.addObject(cy)
                cy.ViewObject.ShapeColor = (0.85, 0.1, 0.1)
                k += 1

    g_r = doc.addObject('App::DocumentObjectGroup', 'Reserved')
    g_r.Label = '예약공간_다음단계(미확정)'
    pil = []
    for s in (+1, -1):
        yb = sorted((s * PILLAR_Y_IN, s * PILLAR_Y_OUT))
        pil.append(box(doc, f'Zone_Pillar_{"L" if s > 0 else "R"}',
                       f'기둥판_예약({"좌" if s > 0 else "우"}, CartRidar 측벽 치수 기준)',
                       App.BoundBox(pb.XMin, yb[0], PLATE_TOP, pb.XMax, yb[1], PLATE_TOP + PILLAR_H), g_r, (0.3, 0.45, 0.95), 85))
    zone_f = box(doc, 'Zone_Front', '전방_예약(OpenCR·TFmini Plus 등, 치수 미입력)',
                 App.BoundBox(zone_j.Shape.BoundBox.XMax + 5, -PILLAR_Y_IN + 1, PLATE_TOP, pb.XMax, PILLAR_Y_IN - 1, PLATE_TOP + 40),
                 g_r, (0.55, 0.3, 0.9), 85)
    gp = doc.addObject('Part::Plane', 'Ground')
    gp.Length, gp.Width = pb.XLength + 120, pb.YLength + 120
    gp.Placement = App.Placement(App.Vector(pb.XMin - 60, pb.YMin - 60, ground_z), App.Rotation())
    gp.Label = f'지면(바퀴 접지, z={ground_z:.2f})'
    g_r.addObject(gp)
    gp.ViewObject.ShapeColor = (0.8, 0.8, 0.8)
    gp.ViewObject.Transparency = 85
    doc.recompute()

    # ---- 5. 로그: 배치 ----
    L(f'\n[3] 배치 결과 (축 높이 z={shaft_z:.2f}, 바퀴 반지름 {WHEEL_D / 2:.2f} -> 지면 z={ground_z:.2f})')
    for tag, lk, plc in motors:
        s = shape_of(lk)
        r = plc.Rotation
        L(f"  {lk.Name}: {fplc(plc)}  로컬X->{tuple(round(v) for v in r.multVec(X))} 로컬Y->{tuple(round(v) for v in r.multVec(Y))} 로컬Z(축)->{tuple(round(v) for v in r.multVec(Z))}")
        L(f"     valid={s.isValid()} solids={len(s.Solids)} {fbb(s.BoundBox)}")
    for tag, wf in wheels:
        L(f"  Wheel_{tag}: valid={wf.Shape.isValid()} {fbb(wf.Shape.BoundBox)}")
    L(f"  Jetson: {fplc(jplc)} valid={jw.isValid()} solids={len(jw.Solids)} {fbb(jwb)}")
    L(f"  밑판  : {fbb(pb)}")
    for z in (zone_j, zone_p, zone_f, *pil):
        L(f"  공간 {z.Label}: {fbb(z.Shape.BoundBox)}")

    # ---- 6. 간섭/간격 검사 ----
    L('\n[5] 간섭 검사 (공통 부피 > 0.001 mm³ 이면 간섭)')
    TH = 1e-3
    ok = lambda v: '간섭' if v > TH else 'OK'
    shp = {tag: shape_of(lk) for tag, lk, _ in motors}
    wsh = {tag: wf.Shape for tag, wf in wheels}
    for tag, s in shp.items():
        v = overlap_volume(s, ps)
        L(f"  모터 {tag} x 밑판 : 공통={v:.4f} {ok(v)}  최소거리={min_dist(s, ps)[0]:.3f} (0=접촉)  밑판 밖 돌출(Y)={max(0, s.BoundBox.YMax - pb.YMax, pb.YMin - s.BoundBox.YMin):.2f}")
    tags = list(shp)
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            v = overlap_volume(shp[tags[i]], shp[tags[j]])
            d, how = min_dist(shp[tags[i]], shp[tags[j]])
            L(f"  모터 {tags[i]} x 모터 {tags[j]}: 공통={v:.4f} {ok(v)}  최소거리={d:.2f} ({how})")
    for tag, s in shp.items():
        v = overlap_volume(s, jw)
        d, how = min_dist(s, jw)
        L(f"  모터 {tag} x Jetson: 공통={v:.4f} {ok(v)}  최소거리={d:.2f} ({how}; bbox는 하한값)")
    for tag, s in shp.items():
        for z in pil:
            d, how = min_dist(s, z.Shape)
            L(f"  모터 {tag} x {z.Label}: 최소거리={d:.2f} ({how})")
    # 바퀴: 동축 원통끼리 distToShape는 피하고 공통 부피 + 축 정렬 바운딩 박스 간격으로 확인
    for tag, w in wsh.items():
        L(f"  바퀴 {tag} x 모터 {tag}: 공통={overlap_volume(w, shp[tag]):.4f} {ok(overlap_volume(w, shp[tag]))}  (혼 바깥면에 접촉)")
        v = overlap_volume(w, ps)
        L(f"  바퀴 {tag} x 밑판 : 공통={v:.4f} {ok(v)}  Y방향 간격={bbox_gap(w.BoundBox, pb):.2f}")
        L(f"  바퀴 {tag} x Jetson: 공통={overlap_volume(w, jw):.4f}  간격(bbox 하한)={bbox_gap(w.BoundBox, jwb):.2f}")
        others = [t for t in shp if t != tag]
        L(f"  바퀴 {tag} x 다른 모터: 공통={sum(overlap_volume(w, shp[t]) for t in others):.4f}")
        L(f"  바퀴 {tag} 최저점 z={shaft_z - WHEEL_D / 2:.3f} (설계값; 바운딩박스 {w.BoundBox.ZMin:.3f}) 지면 z={ground_z:.3f}")
    wt = list(wsh)
    for i in range(len(wt)):
        for j in range(i + 1, len(wt)):
            L(f"  바퀴 {wt[i]} x 바퀴 {wt[j]}: 공통={overlap_volume(wsh[wt[i]], wsh[wt[j]]):.4f}  간격(bbox)={bbox_gap(wsh[wt[i]].BoundBox, wsh[wt[j]].BoundBox):.2f}")
    v = overlap_volume(jw, ps)
    # 밑판에 닿는 것은 하부 프레임이므로 프레임 솔리드 1개와 밑판만 정밀 거리 계산
    fd = fs.distToShape(ps)[0]
    L(f"  Jetson x 밑판: 공통={v:.4f} {ok(v)}  하부프레임-밑판 최소거리={fd:.3f} (0=접촉), Jetson 최저점 z={jwb.ZMin:.3f}")
    for z in pil + [zone_f]:
        L(f"  Jetson 배치공간 x {z.Label}: 공통={overlap_volume(zone_j.Shape, z.Shape):.1f} mm³")
    non_wheel_zmin = min(ps.BoundBox.ZMin, jwb.ZMin, *[s.BoundBox.ZMin for s in shp.values()])
    L(f"  지상고: 밑판 하면 z={pb.ZMin:.2f} - 지면 z={ground_z:.2f} = {pb.ZMin - ground_z:.2f} mm (바퀴 외 최저점 z={non_wheel_zmin:.2f})")
    wy = [w.BoundBox for w in wsh.values()]
    L(f"  전체 폭(바퀴 바깥면) = {max(b.YMax for b in wy) - min(b.YMin for b in wy):.2f} mm, 바퀴 중심 간 거리(좌우) = {2 * (shaft_y + HORN_Z + WHEEL_W / 2):.2f} mm, 앞뒤 축간 거리 = {2 * SHAFT_X:.2f} mm")

    for o in list(doc.Objects):
        if o.TypeId == 'App::DocumentObjectGroup' and not o.Group:
            L(f"  빈 그룹 제거: Name={o.Name} Label={o.Label} InList={[i.Name for i in o.InList]}")
            doc.removeObject(o.Name)

    note = doc.addObject('App::TextDocument', 'DesignNotes')
    note.Label = '설계메모_v3'
    note.Text = NOTES.format(shaft_z=shaft_z, ground=pb.ZMin - ground_z, gap=WHEEL_GAP, w=WHEEL_W)
    doc.recompute()

    v = Gui.ActiveDocument.ActiveView
    v.setCameraType('Orthographic')
    v.viewIsometric(); v.fitAll(); Gui.updateGui()
    doc.saveAs(OUT)
    L(f"\n[6] 저장: {OUT} ({os.path.getsize(OUT)} bytes)")
    L('완료')


NOTES = """TeamRobot 밑판 v3 (자동 생성: build_base_v3.py)

[확정 (사용자 지시)]
- 모터: 후보 B(세움) + 상하 반전. 출력축 쪽 끝면이 밑판에 닿고, 축 높이 = 밑판 하면 기준 {shaft_z:.2f} mm.
- 바퀴: Ø65 일반 바퀴. 지상고(밑판 하면 ~ 지면) {ground:.2f} mm.
- 모터 STEP: XW430 STEP을 XM430 대용으로 사용.
- Jetson: 하부 프레임(375-0137)째로 밑판 위에 고정.

[가정 / 미확정]
1. 바퀴 폭 {w:.0f} mm, 허브 형상 미확정 (혼 바깥면에 붙는 자리표시 원통).
2. 바퀴 안쪽 면 ~ 밑판 측면 간격 {gap:.0f} mm 가정 -> 모터를 v2보다 바깥으로 {gap:.0f} mm 이동.
3. 축 X 위치 ±100 (v2와 동일).
4. Jetson 하부 프레임 STEP에 체결 구멍 없음 -> 고정 방식(가이드 블록, 클램프, 밴드 등) 미정.
5. XM430 실물 커넥터/케이블 위치는 이 STEP으로 확인 불가.
6. 기둥판 위치는 CartRidar.FCStd 측벽 치수를 90° 회전해 가정.
7. 모터 체결구멍은 참조 표시만 있고 밑판에는 가공하지 않음.
"""

try:
    main()
except Exception:
    L('!!! 오류 발생')
    L(traceback.format_exc())
finally:
    logf.close()
    os._exit(0)
