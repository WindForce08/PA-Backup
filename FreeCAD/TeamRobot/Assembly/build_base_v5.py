# -*- coding: utf-8 -*-
"""TeamRobot 밑판 v5 조립 모델 생성 스크립트 (FreeCAD 1.1.x, GUI 모드 필요).

v4 대비 변경:
  - 기둥판-밑판 L브라켓 6개 (기둥판 바깥 면, 장당 3개) + 브라켓/기둥판/밑판 M3 나사홀

v3 대비 변경 (v4에서 반영):
  - 모터 뒤편(아이들러 쪽, 로컬 -Z)을 평평하게 개조한 형상 사용
    (STEP에서 케이스 뒷면 밖으로 튀어나온 부품 제외, 원본 STEP은 그대로 보존)
  - 기둥판 2장 생성: 모터 뒤편에 맞닿는 위치, 모터 케이스 볼트 구멍 위치에 나사홀
  - 밑판: 모터 바닥면 탭 구멍 위치에 나사홀 (PartDesign Pocket)
  - Jetson 하부 프레임용 L자 가이드 블록 4개

실행 (GUI 창 없이):
  FREECAD_USER_HOME=<임시폴더> QT_QPA_PLATFORM=offscreen \
    ~/Application/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage build_base_v5.py

원본(TeamRobot_Base.FCStd, STEP 파일, 이전 버전 조립 파일)은 읽기만 하고 저장하지 않는다.
"""
import os, time, traceback
from collections import Counter
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
import ImportGui

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_BASE = os.path.join(HERE, '..', 'CAD', 'TeamRobot_Base.FCStd')
DXL_STEP = '/home/pa31/Downloads/XW430.N105.I105.STP'
JET_STEP = '/home/pa31/Downloads/Jetson_Orin_Nano_DevKit_3D_STEP_Model/P3766-P3768SKU4-P3767ENVELOPE.stp'
OUT = os.path.join(HERE, 'TeamRobot_Base_v5_Assembly.FCStd')
LOG = os.path.join(HERE, 'build_base_v5.log')

PROTECTED = {os.path.realpath(p) for p in (
    SRC_BASE, DXL_STEP, JET_STEP,
    os.path.join(HERE, 'TeamRobot_Base_v2_Assembly.FCStd'),
    os.path.join(HERE, 'TeamRobot_Base_v3_Assembly.FCStd'),
    os.path.join(HERE, 'TeamRobot_Base_v4_Assembly.FCStd'))}

# ---- 설계 파라미터 ----
SHAFT_X = 100.0          # 구동축 X 위치 (±), 미확정
WHEEL_D = 65.0           # 바퀴 지름 (사용자 지정)
WHEEL_W = 20.0           # 바퀴 폭 (가정)
WHEEL_GAP = 3.0          # 바퀴 안쪽 면 ~ 밑판 측면 간격 (가정)
HUB_RECESS_D, HUB_RECESS_T = 6.0, 3.0
SCREW_CLEAR_D = 2.9      # M2.5 통과 구멍 (ISO 273 medium)
PILLAR_T, PILLAR_H = 5.0, 90.0   # CartRidar.FCStd 측벽 두께/높이
GUIDE_GAP = 0.5          # 가이드 블록 ~ Jetson 하부 프레임 틈새 (가정)
GUIDE_T = 3.0            # 가이드 블록 벽 두께 (가정)
GUIDE_ARM = 15.0         # 가이드 블록 팔 길이 (가정)
GUIDE_H = 4.0            # 가이드 블록 높이 (가정, 프레임 테두리 높이 약 6.5)
MOTOR_MARGIN = 2.0
JET_MARGIN = 5.0
JET_AIR_TOP = 15.0       # 가정
JET_PORT_ACCESS = 30.0   # 가정
# L브라켓 (규격 미지정 -> 가정값)
BR_X = (-43.0, 0.0, 43.0)  # 기둥판당 브라켓 X 위치: 앞뒤 모터 사이 구간(±85.75)을 4등분
BR_T = 3.0               # 두께
BR_LEG_V = 15.0          # 세로 다리 (기둥판 쪽) 높이
BR_LEG_H = 15.0          # 가로 다리 (밑판 쪽) 길이
BR_W = 12.0              # 폭
BR_HOLE_D = 3.4          # M3 통과 구멍 (ISO 273 medium)
M3_HEAD_D = 5.5          # M3 육각 렌치 볼트 머리 지름 (간섭 확인용)
NUT_ALLOW = 4.0          # 기둥판 안쪽 너트 여유 (전방 예약 공간에서 제외)

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


def cyl_axes(shape, radius, axis, sel=None, tol=1e-3):
    """반지름이 radius 이고 축이 axis(X/Y/Z 단위벡터)에 평행한 원통면들의 축 위치 (중복 제거).
    sel(face) 가 주어지면 그 조건을 만족하는 면만 사용 (같은 축 위의 다른 구멍과 섞이지 않게).
    반환: {(축에 수직인 두 좌표): (축 방향 최소, 최대)}"""
    out = {}
    for f in shape.Faces:
        if sel is not None and not sel(f):
            continue
        su = f.Surface
        if not isinstance(su, Part.Cylinder) or abs(su.Radius - radius) > tol:
            continue
        if abs(abs(su.Axis.dot(axis)) - 1) > 1e-6:
            continue
        c = su.Center
        if abs(axis.x) > 0.5:
            key, lo, hi = (round(c.y, 3), round(c.z, 3)), f.BoundBox.XMin, f.BoundBox.XMax
        elif abs(axis.y) > 0.5:
            key, lo, hi = (round(c.x, 3), round(c.z, 3)), f.BoundBox.YMin, f.BoundBox.YMax
        else:
            key, lo, hi = (round(c.x, 3), round(c.y, 3)), f.BoundBox.ZMin, f.BoundBox.ZMax
        a, b = out.get(key, (lo, hi))
        out[key] = (min(a, lo), max(b, hi))
    return out


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


def body_sketch(body, name, label, plc):
    sk = body.newObject('Sketcher::SketchObject', name)
    sk.Label = label
    sk.MapMode = 'Deactivated'
    sk.Placement = plc
    return sk


def add_circles(sk, pts, d):
    """스케치 좌표 (u, v) 에 지름 d 원을 넣고 위치·지름을 구속."""
    for (u, v) in pts:
        i = sk.addGeometry(Part.Circle(App.Vector(u, v, 0), App.Vector(0, 0, 1), d / 2), False)
        sk.addConstraint(Sketcher.Constraint('Diameter', i, d))
        sk.addConstraint(Sketcher.Constraint('DistanceX', -1, 1, i, 3, u))
        sk.addConstraint(Sketcher.Constraint('DistanceY', -1, 1, i, 3, v))


def check_circles(sk, pts, d):
    circ = [g for g in sk.Geometry if isinstance(g, Part.Circle)]
    assert len(circ) == len(pts), f'{sk.Name}: 원 개수 불일치'
    err = max(max(abs(g.Center.x - u), abs(g.Center.y - v), abs(g.Radius * 2 - d)) for g, (u, v) in zip(circ, pts))
    return err


def through_pocket(body, name, label, sk):
    pk = body.newObject('PartDesign::Pocket', name)
    pk.Label = label
    pk.Profile = sk
    pk.Type = 'ThroughAll'
    if hasattr(pk, 'SideType'):
        pk.SideType = 'Symmetric'
    else:
        pk.Midplane = True
    pk.Refine = False
    sk.ViewObject.Visibility = False
    return pk


def main():
    L('=== TeamRobot 밑판 v5 생성 ===')
    L('FreeCAD', '.'.join(App.Version()[:3]), App.Version()[3])
    L('시각', time.strftime('%Y-%m-%d %H:%M:%S'))
    if os.path.realpath(OUT) in PROTECTED:
        raise RuntimeError('출력 경로가 보호 대상 파일과 같음')
    L('\n[0] 입력 파일')
    for p in (SRC_BASE, DXL_STEP, JET_STEP):
        if not os.path.isfile(p):
            raise FileNotFoundError(p)
        L(f"  OK {os.path.realpath(p)} ({os.path.getsize(p)} bytes, 수정 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p)))})")

    doc = App.newDocument('TeamRobot_Base_v5')
    doc.Label = 'TeamRobot_Base_v5_Assembly'
    X, Y, Z = App.Vector(1, 0, 0), App.Vector(0, 1, 0), App.Vector(0, 0, 1)

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
    plate.Label = '밑판_270x250x5'
    doc.recompute()
    L(f"  원본 Body: vol={ref_vol:.1f} {fbb(ref_bb)}")
    L(f"  복사본   : vol={plate.Shape.Volume:.1f} {fbb(plate.Shape.BoundBox)} valid={plate.Shape.isValid()} Tip={plate.Tip.Name}")
    assert abs(plate.Shape.Volume - ref_vol) < 1e-6, '복사 후 밑판 부피 불일치'
    pb = plate.Shape.BoundBox
    PLATE_TOP = pb.ZMax
    plate.ViewObject.ShapeColor = (0.55, 0.62, 0.70)

    # ---- 2. STEP 원본 ----
    L('\n[2] STEP 가져오기 (원본은 숨김 그룹에 보존)')
    g_src = doc.addObject('App::DocumentObjectGroup', 'STEP_Originals')
    g_src.Label = 'STEP_원본_수정금지(숨김)'
    dxl_root, dxl_new = import_step(doc, DXL_STEP)
    jet_root, jet_new = import_step(doc, JET_STEP)
    g_src.addObject(dxl_root)
    g_src.addObject(jet_root)
    dxl_root.ViewObject.Visibility = False
    jet_root.ViewObject.Visibility = False

    by_label = {o.Label: o for o in dxl_new}
    caseM = shape_of(by_label['DC12_C04_CASE_M_DUMMY'])
    caseB3 = shape_of(by_label['DC12_C04_CASE_B3_DUMMY'])
    caseF = shape_of(by_label['DC12_C04_CASE_F_DUMMY'])
    case_bb = Part.makeCompound([caseM, caseB3, caseF]).BoundBox
    HORN_Z = shape_of(by_label['HN12_N105_DUMMY']).BoundBox.ZMax
    L(f"  DXL 케이스: {fbb(case_bb)}  혼 바깥면 로컬 Z={HORN_Z:.2f}")

    # 모터 체결 구멍 (STEP 형상에서 직접 측정)
    end_holes = cyl_axes(caseM, 1.025, Y, sel=lambda f: f.BoundBox.YMin > 0)          # 로컬 +Y 끝면 (축 쪽)
    bolt_holes = cyl_axes(caseB3, 1.25, Z)                                              # 케이스 조립 볼트 관통홀
    f_thread = cyl_axes(caseF, 1.025, Z)
    L(f"  +Y 끝면 탭 구멍(Ø2.05) 축 (X,Z): {sorted(end_holes)}  깊이: 끝면 {case_bb.YMax:.2f} -> 바닥 {min(v[0] for v in end_holes.values()):.2f} = {case_bb.YMax - min(v[0] for v in end_holes.values()):.2f} mm")
    L(f"  케이스 조립 볼트 관통홀(B3, Ø2.5) 축 (X,Y): {sorted(bolt_holes)}  B3 범위 Z{[tuple(round(x, 2) for x in v) for v in bolt_holes.values()][0]}")
    L(f"  케이스 볼트 나사부(F, Ø2.05) Z 범위: {[tuple(round(x, 2) for x in v) for v in f_thread.values()][0]}")
    bolts = [o for o in dxl_new if o.Label.startswith('WBH_M2_5X') and o.Label != 'WBH_M2_5X8']
    L(f"  케이스 조립 볼트 부품: {[o.Label for o in bolts]}  {fbb(shape_of(bolts[0]).BoundBox)}")
    assert len(end_holes) == 4 and len(bolt_holes) == 4, '구멍 개수 불일치'

    # ---- 3. 뒤편 평면 개조형 모터 정의 ----
    L('\n[3] 개조형 모터 (뒤편 평면)')
    g_def = doc.addObject('App::DocumentObjectGroup', 'Derived')
    g_def.Label = '개조형_모터_정의(숨김)'
    dmod = doc.addObject('App::Part', 'DXL_Modified')
    dmod.Label = 'DXL_개조형_뒤편평면(XW430 STEP 기반)'
    g_def.addObject(dmod)
    kept, dropped = [], []
    for c in dxl_root.Group:
        if c.TypeId not in ('Part::Feature', 'App::Part'):
            continue
        s = shape_of(c)
        if s.isNull() or not s.Solids:
            continue
        if s.BoundBox.ZMin < case_bb.ZMin - 1e-6:
            dropped.append((c.Label, round(s.BoundBox.ZMin, 2)))
            continue
        lk = doc.addObject('App::Link', f'Mod_{c.Name}')
        lk.LinkedObject = c
        lk.Placement = c.Placement
        lk.Label = f'개조형_{c.Label}'
        dmod.addObject(lk)
        kept.append(c.Label)
    doc.recompute()
    dmod_s = shape_of(dmod)
    L(f"  유지: {kept}")
    L(f"  제외(케이스 뒷면 Z={case_bb.ZMin:.2f} 밖으로 돌출): {dropped}")
    L(f"  개조형 모터: solids={len(dmod_s.Solids)} valid={dmod_s.isValid()} {fbb(dmod_s.BoundBox)}")
    assert abs(dmod_s.BoundBox.ZMin - case_bb.ZMin) < 1e-6
    dmod.ViewObject.Visibility = False

    # ---- 4. 모터·바퀴 배치 (v3와 동일: 후보 B 세움 + 상하 반전) ----
    shaft_y = pb.YMax + WHEEL_GAP - HORN_Z
    shaft_z = PLATE_TOP + case_bb.YMax
    ground_z = shaft_z - WHEEL_D / 2
    g_m = doc.addObject('App::DocumentObjectGroup', 'Motors')
    g_m.Label = '모터_개조형(XM430 대용)'
    g_w = doc.addObject('App::DocumentObjectGroup', 'Wheels')
    g_w.Label = f'바퀴_Ø{WHEEL_D:.0f}_일반(폭 {WHEEL_W:.0f} 가정)'
    motors, wheels = [], []
    for tag, sx, sy in [('FL', +1, +1), ('FR', +1, -1), ('RL', -1, +1), ('RR', -1, -1)]:
        zm, ym = Y * sy, Z * -1
        plc = App.Placement(App.Vector(sx * SHAFT_X, sy * shaft_y, shaft_z), rot_from_axes(ym.cross(zm), ym, zm))
        lk = doc.addObject('App::Link', f'DXL_{tag}')
        lk.LinkedObject = dmod
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
        w = Part.makeCylinder(WHEEL_D / 2, WHEEL_W, App.Vector(0, 0, HORN_Z))
        w = w.cut(Part.makeCylinder(HUB_RECESS_D / 2, HUB_RECESS_T, App.Vector(0, 0, HORN_Z)))
        w.Placement = plc
        wheels.append((tag, feature(doc, f'Wheel_{tag}', f'바퀴_{tag}(Ø{WHEEL_D:.0f}x{WHEEL_W:.0f}, 허브 미확정)', w, g_w, (0.15, 0.15, 0.15))))
        motors.append((tag, lk, plc, sx, sy))

    # ---- 5. 밑판 나사홀: 모터 바닥면(+Y 끝면) 탭 구멍 위치 ----
    L('\n[5] 밑판 나사홀 (모터-밑판)')
    plate_pts = []
    for tag, lk, plc, sx, sy in motors:
        for (hx, hz) in sorted(end_holes):
            w = plc.multVec(App.Vector(hx, case_bb.YMax, hz))
            assert abs(w.z - PLATE_TOP) < 1e-6
            plate_pts.append((round(w.x, 6), round(w.y, 6)))
    sk = body_sketch(plate, 'MotorScrewSketch', f'모터체결홀_스케치(Ø{SCREW_CLEAR_D})',
                     App.Placement(App.Vector(0, 0, PLATE_TOP), App.Rotation()))
    add_circles(sk, plate_pts, SCREW_CLEAR_D)
    pk = through_pocket(plate, 'MotorScrewHoles', f'모터체결홀_M2.5_Ø{SCREW_CLEAR_D}x{len(plate_pts)}', sk)
    doc.recompute()
    L(f"  구멍 {len(plate_pts)}개, 스케치 위치 오차 {check_circles(sk, plate_pts, SCREW_CLEAR_D):.2e}, Pocket Type={pk.Type}, Tip={plate.Tip.Name}")
    for tag, lk, plc, sx, sy in motors:
        L(f"    {tag}: {[tuple(round(c, 2) for c in p) for p in plate_pts if (p[0] > 0) == (sx > 0) and (p[1] > 0) == (sy > 0)]}")
    exp_vol = ref_vol - len(plate_pts) * 3.141592653589793 * (SCREW_CLEAR_D / 2) ** 2 * (PLATE_TOP - pb.ZMin)
    ps = plate.Shape
    L(f"  밑판 부피 {ps.Volume:.2f} (예상 {exp_vol:.2f}) valid={ps.isValid()} solids={len(ps.Solids)}")
    assert abs(ps.Volume - exp_vol) < 0.01 and ps.isValid() and len(ps.Solids) == 1

    # ---- 6. 기둥판 2장: 모터 뒤편에 맞닿음 + 케이스 볼트 구멍 위치 나사홀 ----
    L('\n[6] 기둥판 (모터 뒤편-기둥 나사홀)')
    g_p = doc.addObject('App::DocumentObjectGroup', 'Pillars')
    g_p.Label = f'기둥판_{PILLAR_T:.0f}x{PILLAR_H:.0f}'
    pillars, pillar_motor_pts = {}, {}
    for side, sy in (('L', +1), ('R', -1)):
        ms = [m for m in motors if m[4] == sy]
        back_y = [m[2].multVec(App.Vector(0, 0, case_bb.ZMin)).y for m in ms]
        assert abs(back_y[0] - back_y[1]) < 1e-9
        y_out = back_y[0]                               # 기둥판 바깥 면 = 모터 뒷면
        y_in = y_out - sy * PILLAR_T
        y0 = min(y_in, y_out)
        b = doc.addObject('PartDesign::Body', f'Pillar_{side}')
        b.Label = f'기둥판_{"좌" if sy > 0 else "우"}'
        g_p.addObject(b)
        bx = b.newObject('PartDesign::AdditiveBox', f'PillarBox_{side}')
        bx.Length, bx.Width, bx.Height = pb.XLength, PILLAR_T, PILLAR_H
        bx.MapMode = 'Deactivated'
        bx.Placement = App.Placement(App.Vector(pb.XMin, y0, PLATE_TOP), App.Rotation())
        pts = []
        for tag, lk, plc, sx, _ in ms:
            for (hx, hy) in sorted(bolt_holes):
                w = plc.multVec(App.Vector(hx, hy, case_bb.ZMin))
                assert abs(w.y - y_out) < 1e-6
                pts.append((round(w.x, 6), round(w.z, 6)))
        # 스케치 평면: 로컬 x -> X, 로컬 y -> Z, 법선 -> -Y, 기둥판 두께 중앙
        skp = body_sketch(b, f'PillarScrewSketch_{side}', f'기둥판_모터체결홀_스케치_{side}',
                          App.Placement(App.Vector(0, (y_in + y_out) / 2, 0), rot_from_axes(X, Z, Y * -1)))
        add_circles(skp, pts, SCREW_CLEAR_D)
        pkp = through_pocket(b, f'PillarScrewHoles_{side}', f'모터체결홀_M2.5_Ø{SCREW_CLEAR_D}x{len(pts)}', skp)
        doc.recompute()
        s = b.Shape
        L(f"  기둥판_{side}: {fbb(s.BoundBox)} valid={s.isValid()} solids={len(s.Solids)} 스케치 오차 {check_circles(skp, pts, SCREW_CLEAR_D):.2e}")
        L(f"    구멍 (X,Z): {[tuple(round(c, 2) for c in p) for p in pts]}  최저 구멍 하단 z={min(p[1] for p in pts) - SCREW_CLEAR_D / 2:.2f} (밑판 상면 {PLATE_TOP:.2f})")
        b.ViewObject.ShapeColor = (0.45, 0.55, 0.85)
        b.ViewObject.Transparency = 40
        pillars[side] = b
        pillar_motor_pts[side] = pts

    # ---- 6b. 기둥판-밑판 L브라켓 ----
    L('\n[6b] 기둥판-밑판 L브라켓 (기둥판 바깥 면 = 모터 쪽)')
    g_b = doc.addObject('App::DocumentObjectGroup', 'Brackets')
    g_b.Label = f'L브라켓_{BR_LEG_V:.0f}x{BR_LEG_H:.0f}x{BR_W:.0f}_t{BR_T:.0f}_M3'
    brackets, plate_br_pts, pillar_br_pts = [], [], {}
    zv = PLATE_TOP + BR_T + (BR_LEG_V - BR_T) / 2          # 세로 다리 구멍 높이
    for side, sy in (('L', +1), ('R', -1)):
        pbb = pillars[side].Shape.BoundBox
        y_o = pbb.YMax if sy > 0 else pbb.YMin              # 기둥판 바깥 면
        yhc = y_o + sy * (BR_T + (BR_LEG_H - BR_T) / 2)      # 가로 다리 구멍 위치
        pillar_br_pts[side] = []
        for i, xc in enumerate(BR_X):
            tag = f'{side}{i + 1}'
            b = doc.addObject('PartDesign::Body', f'Bracket_{tag}')
            b.Label = f'L브라켓_{"좌" if sy > 0 else "우"}{i + 1}(X={xc:+.0f})'
            g_b.addObject(b)
            yv = sorted((y_o, y_o + sy * BR_T))
            lv = b.newObject('PartDesign::AdditiveBox', f'BrLegV_{tag}')
            lv.Length, lv.Width, lv.Height = BR_W, BR_T, BR_LEG_V
            lv.MapMode = 'Deactivated'
            lv.Placement = App.Placement(App.Vector(xc - BR_W / 2, yv[0], PLATE_TOP), App.Rotation())
            yh = sorted((y_o, y_o + sy * BR_LEG_H))
            lh = b.newObject('PartDesign::AdditiveBox', f'BrLegH_{tag}')
            lh.Length, lh.Width, lh.Height = BR_W, BR_LEG_H, BR_T
            lh.MapMode = 'Deactivated'
            lh.Placement = App.Placement(App.Vector(xc - BR_W / 2, yh[0], PLATE_TOP), App.Rotation())
            cv = b.newObject('PartDesign::SubtractiveCylinder', f'BrHoleV_{tag}')
            cv.Radius, cv.Height = BR_HOLE_D / 2, BR_T + 2
            cv.MapMode = 'Deactivated'
            cv.Placement = App.Placement(App.Vector(xc, yv[0] - 1, zv), App.Rotation(X, -90))   # 축 -> +Y
            ch = b.newObject('PartDesign::SubtractiveCylinder', f'BrHoleH_{tag}')
            ch.Radius, ch.Height = BR_HOLE_D / 2, BR_T + 2
            ch.MapMode = 'Deactivated'
            ch.Placement = App.Placement(App.Vector(xc, yhc, PLATE_TOP - 1), App.Rotation())
            b.ViewObject.ShapeColor = (0.75, 0.75, 0.78)
            brackets.append((tag, side, sy, b, xc, yhc))
            plate_br_pts.append((xc, yhc))
            pillar_br_pts[side].append((xc, zv))
    # 기둥판 구멍
    for side, sy in (('L', +1), ('R', -1)):
        b = pillars[side]
        pbb = b.Shape.BoundBox
        skb = body_sketch(b, f'PillarBracketSketch_{side}', f'기둥판_브라켓홀_스케치_{side}',
                          App.Placement(App.Vector(0, (pbb.YMin + pbb.YMax) / 2, 0), rot_from_axes(X, Z, Y * -1)))
        add_circles(skb, pillar_br_pts[side], BR_HOLE_D)
        through_pocket(b, f'PillarBracketHoles_{side}', f'브라켓체결홀_M3_Ø{BR_HOLE_D}x{len(pillar_br_pts[side])}', skb)
    # 밑판 구멍
    skm = body_sketch(plate, 'BracketScrewSketch', f'브라켓체결홀_스케치(Ø{BR_HOLE_D})',
                      App.Placement(App.Vector(0, 0, PLATE_TOP), App.Rotation()))
    add_circles(skm, plate_br_pts, BR_HOLE_D)
    through_pocket(plate, 'BracketScrewHoles', f'브라켓체결홀_M3_Ø{BR_HOLE_D}x{len(plate_br_pts)}', skm)
    doc.recompute()
    ps = plate.Shape
    hole_v = lambda d, t: 3.141592653589793 * (d / 2) ** 2 * t
    exp_plate = exp_vol - len(plate_br_pts) * hole_v(BR_HOLE_D, PLATE_TOP - pb.ZMin)
    L(f"  밑판: 부피 {ps.Volume:.2f} (예상 {exp_plate:.2f}) valid={ps.isValid()} solids={len(ps.Solids)} Tip={plate.Tip.Name} 스케치 오차 {check_circles(skm, plate_br_pts, BR_HOLE_D):.2e}")
    assert abs(ps.Volume - exp_plate) < 0.01 and ps.isValid() and len(ps.Solids) == 1
    for side in ('L', 'R'):
        s = pillars[side].Shape
        exp_p = pb.XLength * PILLAR_T * PILLAR_H - 8 * hole_v(SCREW_CLEAR_D, PILLAR_T) - len(pillar_br_pts[side]) * hole_v(BR_HOLE_D, PILLAR_T)
        L(f"  기둥판_{side}: 부피 {s.Volume:.2f} (예상 {exp_p:.2f}) valid={s.isValid()} solids={len(s.Solids)} 브라켓홀 (X,Z)={pillar_br_pts[side]}")
        assert abs(s.Volume - exp_p) < 0.01 and s.isValid() and len(s.Solids) == 1
    exp_b = BR_W * (BR_T * BR_LEG_V + (BR_LEG_H - BR_T) * BR_T) - 2 * hole_v(BR_HOLE_D, BR_T)
    for tag, side, sy, b, xc, yhc in brackets:
        s = b.Shape
        L(f"  {b.Label}: {fbb(s.BoundBox)} valid={s.isValid()} solids={len(s.Solids)} 부피 {s.Volume:.2f} (예상 {exp_b:.2f}) 밑판홀 (X,Y)=({xc:.2f},{yhc:.2f}) 기둥홀 (X,Z)=({xc:.2f},{zv:.2f})")
        assert abs(s.Volume - exp_b) < 0.01 and s.isValid() and len(s.Solids) == 1
    # 구멍 사이 최소 간격 (가장자리 기준)
    def edge_gap(pa, da, pbs, db):
        return min(((pa[0] - q[0]) ** 2 + (pa[1] - q[1]) ** 2) ** 0.5 for q in pbs) - (da + db) / 2
    L(f"  밑판: 브라켓홀 ~ 모터홀 최소 가장자리 간격 {min(edge_gap(p, BR_HOLE_D, plate_pts, SCREW_CLEAR_D) for p in plate_br_pts):.2f} mm,"
      f" 브라켓홀 ~ 기둥판 바깥 면 {min(abs(abs(p[1]) - abs(pillars['L'].Shape.BoundBox.YMax)) for p in plate_br_pts) - BR_HOLE_D / 2:.2f} mm,"
      f" ~ 밑판 가장자리 {min(pb.YMax - abs(p[1]) for p in plate_br_pts) - BR_HOLE_D / 2:.2f} mm")
    L(f"  기둥판: 브라켓홀 하단 z={zv - BR_HOLE_D / 2:.2f} (기둥판 하면 {PLATE_TOP:.2f}),"
      f" 모터홀과 최소 가장자리 간격 {min(edge_gap(p, BR_HOLE_D, pillar_motor_pts[sd], SCREW_CLEAR_D) for sd in ('L', 'R') for p in pillar_br_pts[sd]):.2f} mm")
    L(f"  볼트 머리(Ø{M3_HEAD_D}) 여유: 세로 다리 머리 하단 z={zv - M3_HEAD_D / 2:.2f} > 가로 다리 상면 z={PLATE_TOP + BR_T:.2f},"
      f" 가로 다리 머리 ~ 세로 다리 바깥 면 {(BR_LEG_H - BR_T) / 2 - M3_HEAD_D / 2:.2f} mm, 머리 ~ 가로 다리 끝 {(BR_LEG_H - BR_T) / 2 - M3_HEAD_D / 2:.2f} mm")

    # ---- 7. Jetson + 가이드 블록 ----
    L('\n[7] Jetson 하부 프레임 가이드 블록')
    g_j = doc.addObject('App::DocumentObjectGroup', 'JetsonGroup')
    g_j.Label = 'Jetson_OrinNano(하부 프레임 + 가이드 블록)'
    jbb = shape_of(jet_root).BoundBox
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
    frame_obj = [o for o in jet_new if o.Label == '375-0137-000'][0]
    fs = shape_of(frame_obj).copy()
    fs.transformShape(jplc.toMatrix())
    fb = fs.optimalBoundingBox() if hasattr(fs, 'optimalBoundingBox') else fs.BoundBox
    L(f"  하부 프레임(375-0137) 월드: {fbb(fb)}")
    # 프레임 윤곽 밖으로 튀어나온 Jetson 부품의 최저 높이 (가이드 블록 높이 제한 확인)
    for nm, test in (('후방(-X)', lambda b: b.XMin < fb.XMin - 1e-6), ('전방(+X)', lambda b: b.XMax > fb.XMax + 1e-6),
                     ('우(-Y)', lambda b: b.YMin < fb.YMin - 1e-6), ('좌(+Y)', lambda b: b.YMax > fb.YMax + 1e-6)):
        out = [s.BoundBox for s in jw.Solids if test(s.BoundBox)]
        L(f"    프레임 밖 {nm} 돌출 솔리드 {len(out)}개" + (f", 최저 z={min(b.ZMin for b in out):.2f}" if out else ''))
    guides = []
    for (fx, sx, nx) in ((fb.XMin, -1, '후'), (fb.XMax, +1, '전')):
        for (fy, sy, ny) in ((fb.YMin, -1, '우'), (fb.YMax, +1, '좌')):
            p0x, p0y = fx + sx * GUIDE_GAP, fy + sy * GUIDE_GAP
            uv = [(0, -GUIDE_ARM), (GUIDE_T, -GUIDE_ARM), (GUIDE_T, GUIDE_T), (-GUIDE_ARM, GUIDE_T), (-GUIDE_ARM, 0), (0, 0)]
            pts = [App.Vector(p0x + sx * u, p0y + sy * v, 0) for u, v in uv]
            tag = ('R' if sx < 0 else 'F') + ('R' if sy < 0 else 'L')
            b = doc.addObject('PartDesign::Body', f'GuideBlock_{tag}')
            b.Label = f'Jetson_가이드블록_{nx}{ny}'
            g_j.addObject(b)
            skg = body_sketch(b, f'GuideSketch_{tag}', f'가이드블록_스케치_{tag}', App.Placement(App.Vector(0, 0, PLATE_TOP), App.Rotation()))
            n = len(pts)
            for i in range(n):
                skg.addGeometry(Part.LineSegment(pts[i], pts[(i + 1) % n]), False)
            for i in range(n):
                skg.addConstraint(Sketcher.Constraint('Coincident', i, 2, (i + 1) % n, 1))
            pd = b.newObject('PartDesign::Pad', f'GuidePad_{tag}')
            pd.Profile = skg
            pd.Length = GUIDE_H
            skg.ViewObject.Visibility = False
            b.ViewObject.ShapeColor = (0.95, 0.45, 0.1)
            guides.append((tag, b))
    doc.recompute()
    for tag, b in guides:
        L(f"  {b.Label}: {fbb(b.Shape.BoundBox)} valid={b.Shape.isValid()} vol={b.Shape.Volume:.1f}")

    zone_j = box(doc, 'Zone_Jetson', 'Jetson_배치공간(측면+5, 상부+15 가정)',
                 grow(jwb, JET_MARGIN, JET_MARGIN, JET_AIR_TOP, zmin=PLATE_TOP), g_j, (0.2, 0.75, 0.3), 85)
    zone_p = box(doc, 'Zone_JetsonPorts', f'Jetson_IO커넥터_접근공간({JET_PORT_ACCESS:.0f}mm 가정)',
                 App.BoundBox(pb.XMin, jwb.YMin, PLATE_TOP, jwb.XMin, jwb.YMax, jwb.ZMax), g_j, (0.95, 0.85, 0.2), 85)
    for tag, lk, plc, sx, sy in motors:
        box(doc, f'Zone_{tag}', f'모터장착공간_{tag}(+{MOTOR_MARGIN:.0f}mm)',
            grow(shape_of(lk).BoundBox, MOTOR_MARGIN, MOTOR_MARGIN, MOTOR_MARGIN, zmin=PLATE_TOP), g_m, (1.0, 0.55, 0.1), 85)

    g_r = doc.addObject('App::DocumentObjectGroup', 'Reserved')
    g_r.Label = '예약공간_다음단계(미확정)'
    pil_in = min(abs(pillars['L'].Shape.BoundBox.YMin), abs(pillars['R'].Shape.BoundBox.YMax))
    zone_f = box(doc, 'Zone_Front', '전방_예약(OpenCR·TFmini Plus 등, 치수 미입력)',
                 App.BoundBox(zone_j.Shape.BoundBox.XMax + 5, -pil_in + NUT_ALLOW, PLATE_TOP, pb.XMax, pil_in - NUT_ALLOW, PLATE_TOP + 40),
                 g_r, (0.55, 0.3, 0.9), 85)
    gp = doc.addObject('Part::Plane', 'Ground')
    gp.Length, gp.Width = pb.XLength + 120, pb.YLength + 120
    gp.Placement = App.Placement(App.Vector(pb.XMin - 60, pb.YMin - 60, ground_z), App.Rotation())
    gp.Label = f'지면(바퀴 접지, z={ground_z:.2f})'
    g_r.addObject(gp)
    gp.ViewObject.ShapeColor = (0.8, 0.8, 0.8)
    gp.ViewObject.Transparency = 85
    doc.recompute()

    # ---- 8. 배치 로그 ----
    L(f'\n[8] 배치 결과 (축 높이 z={shaft_z:.2f}, 지면 z={ground_z:.2f})')
    shp = {}
    for tag, lk, plc, sx, sy in motors:
        s = shape_of(lk)
        shp[tag] = s
        L(f"  {lk.Name}: {fplc(plc)} valid={s.isValid()} solids={len(s.Solids)} {fbb(s.BoundBox)}")
    wsh = {tag: wf.Shape for tag, wf in wheels}
    for tag, w in wsh.items():
        L(f"  Wheel_{tag}: {fbb(w.BoundBox)}")
    L(f"  Jetson: {fplc(jplc)} valid={jw.isValid()} {fbb(jwb)}")
    for side, b in pillars.items():
        L(f"  기둥판_{side}: {fbb(b.Shape.BoundBox)}")
    L(f"  밑판: {fbb(ps.BoundBox)}")

    # ---- 9. 구멍 정렬 검사 (실제 형상끼리 비교) ----
    L('\n[9] 나사홀 정렬 검사')
    plate_h = cyl_axes(ps, SCREW_CLEAR_D / 2, Z)
    worst = 0.0
    for tag, s in shp.items():
        mh = list(cyl_axes(s, 1.025, Z, sel=lambda f: PLATE_TOP < f.BoundBox.ZMax <= PLATE_TOP + 3.5))
        dev = [min(((k[0] - p[0]) ** 2 + (k[1] - p[1]) ** 2) ** 0.5 for p in plate_h) for k in mh]
        worst = max(worst, max(dev))
        L(f"  모터 {tag} 바닥 탭 구멍 {len(mh)}개 <-> 밑판 구멍: 최대 축 편차 {max(dev):.2e} mm")
    for side, b in pillars.items():
        ph = cyl_axes(b.Shape, SCREW_CLEAR_D / 2, Y)
        y_face = b.Shape.BoundBox.YMax if side == 'L' else b.Shape.BoundBox.YMin
        for tag, s in shp.items():
            if (s.BoundBox.YMin > 0) != (side == 'L'):
                continue
            # 기둥판 면에서 10 mm 이내에 걸친 Ø2.5 관통홀만 (혼 쪽 구멍 제외)
            mh = list(cyl_axes(s, 1.25, Y, sel=lambda f: min(abs(f.BoundBox.YMin - y_face), abs(f.BoundBox.YMax - y_face)) < 10
                                                         and f.BoundBox.YLength < 10))
            dev = [min(((k[0] - p[0]) ** 2 + (k[1] - p[1]) ** 2) ** 0.5 for p in ph) for k in mh]
            worst = max(worst, max(dev))
            L(f"  모터 {tag} 케이스 볼트 관통홀 {len(mh)}개 <-> 기둥판_{side} 구멍: 최대 축 편차 {max(dev):.2e} mm")
    plate_bh = cyl_axes(ps, BR_HOLE_D / 2, Z)
    for tag, side, sy, b, xc, yhc in brackets:
        bh = list(cyl_axes(b.Shape, BR_HOLE_D / 2, Z))
        bv = list(cyl_axes(b.Shape, BR_HOLE_D / 2, Y))
        pv = cyl_axes(pillars[side].Shape, BR_HOLE_D / 2, Y)
        d1 = max(min(((k[0] - p[0]) ** 2 + (k[1] - p[1]) ** 2) ** 0.5 for p in plate_bh) for k in bh)
        d2 = max(min(((k[0] - p[0]) ** 2 + (k[1] - p[1]) ** 2) ** 0.5 for p in pv) for k in bv)
        worst = max(worst, d1, d2)
        L(f"  브라켓 {tag}: 가로 다리 구멍 {len(bh)}개 <-> 밑판 편차 {d1:.2e}, 세로 다리 구멍 {len(bv)}개 <-> 기둥판_{side} 편차 {d2:.2e}")
    L(f"  최대 편차 {worst:.2e} mm {'OK' if worst < 1e-6 else '확인 필요'}")

    # ---- 10. 간섭 검사 ----
    L('\n[10] 간섭 검사 (공통 부피 > 0.001 mm³ 이면 간섭)')
    L('  ※ 동축 원통이 많은 쌍(나사홀-모터, 바퀴-혼)은 distToShape 대신 공통 부피 + 축 정렬 바운딩 박스로 판정')
    TH = 1e-3
    ok = lambda v: '간섭' if v > TH else 'OK'
    for tag, s in shp.items():
        v = overlap_volume(s, ps)
        L(f"  모터 {tag} x 밑판: 공통={v:.4f} {ok(v)}  모터 최저 z={s.BoundBox.ZMin:.3f} (밑판 상면 {PLATE_TOP:.3f})")
        side = 'L' if s.BoundBox.YMin > 0 else 'R'
        pbx = pillars[side].Shape
        v = overlap_volume(s, pbx)
        gap = (s.BoundBox.YMin - pbx.BoundBox.YMax) if side == 'L' else (pbx.BoundBox.YMin - s.BoundBox.YMax)
        L(f"  모터 {tag} x 기둥판_{side}: 공통={v:.4f} {ok(v)}  Y 간격={gap:.3f} (0=맞닿음)")
        v = overlap_volume(s, jw)
        L(f"  모터 {tag} x Jetson: 공통={v:.4f} {ok(v)}  간격(bbox 하한)={bbox_gap(s.BoundBox, jwb):.2f}")
    tags = list(shp)
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            v = overlap_volume(shp[tags[i]], shp[tags[j]])
            L(f"  모터 {tags[i]} x 모터 {tags[j]}: 공통={v:.4f} {ok(v)}  간격(bbox)={bbox_gap(shp[tags[i]].BoundBox, shp[tags[j]].BoundBox):.2f}")
    for tag, w in wsh.items():
        L(f"  바퀴 {tag} x 모터 {tag}: 공통={overlap_volume(w, shp[tag]):.4f}  x 밑판: 공통={overlap_volume(w, ps):.4f} Y간격={bbox_gap(w.BoundBox, ps.BoundBox):.2f}"
          f"  x 기둥판: 공통={sum(overlap_volume(w, b.Shape) for b in pillars.values()):.4f}  최저점 z={shaft_z - WHEEL_D / 2:.3f}")
    for side, b in pillars.items():
        s = b.Shape
        L(f"  기둥판_{side} x 밑판: 공통={overlap_volume(s, ps):.4f} {ok(overlap_volume(s, ps))}  기둥판 하면 z={s.BoundBox.ZMin:.3f}")
        L(f"  기둥판_{side} x Jetson: 공통={overlap_volume(s, jw):.4f}  간격(bbox 하한)={bbox_gap(s.BoundBox, jwb):.2f}")
        L(f"  기둥판_{side} x 밑판 나사홀: 기둥판 발자국 안의 밑판 구멍 {sum(1 for p in plate_pts if s.BoundBox.YMin <= p[1] <= s.BoundBox.YMax)}개")
    v = overlap_volume(jw, ps)
    L(f"  Jetson x 밑판: 공통={v:.4f} {ok(v)}  하부프레임-밑판 최소거리={fs.distToShape(ps)[0]:.3f} (0=접촉)")
    for tag, b in guides:
        s = b.Shape
        v1, v2 = overlap_volume(s, jw), overlap_volume(s, ps)
        d = fs.distToShape(s)[0]
        L(f"  가이드 {tag} x Jetson: 공통={v1:.4f} {ok(v1)}  하부프레임까지 최소거리={d:.3f}  x 밑판: 공통={v2:.4f} {ok(v2)}")
        for side, pbody in pillars.items():
            if overlap_volume(s, pbody.Shape) > TH:
                L(f"  [주의] 가이드 {tag} x 기둥판_{side} 겹침")
    bsh = {tag: (side, b.Shape) for tag, side, sy, b, xc, yhc in brackets}
    for tag, (side, s) in bsh.items():
        pbx = pillars[side].Shape
        v1, v2 = overlap_volume(s, ps), overlap_volume(s, pbx)
        gy = (s.BoundBox.YMin - pbx.BoundBox.YMax) if side == 'L' else (pbx.BoundBox.YMin - s.BoundBox.YMax)
        others = [(n, overlap_volume(s, x)) for n, x in list(shp.items()) + list(wsh.items())]
        mg = min(bbox_gap(s.BoundBox, shp[t].BoundBox) for t in shp)
        L(f"  브라켓 {tag} x 밑판: 공통={v1:.4f} {ok(v1)} 하면 z={s.BoundBox.ZMin:.3f} | x 기둥판_{side}: 공통={v2:.4f} {ok(v2)} Y 간격={gy:.3f}"
          f" | x 모터/바퀴 공통 합={sum(v for _, v in others):.4f} 모터까지 간격(bbox)={mg:.2f}"
          f" | x Jetson 공통={overlap_volume(s, jw):.4f} | x 가이드 공통={sum(overlap_volume(s, g.Shape) for _, g in guides):.4f}")
    bt = list(bsh)
    L(f"  브라켓끼리 공통 합={sum(overlap_volume(bsh[bt[i]][1], bsh[bt[j]][1]) for i in range(len(bt)) for j in range(i + 1, len(bt))):.4f}")
    L(f"  전방 예약 공간: Y ±{pil_in - NUT_ALLOW:.2f} (기둥판 안쪽 너트 여유 {NUT_ALLOW} 제외)")
    L(f"  지상고: 밑판 하면 z={ps.BoundBox.ZMin:.2f} - 지면 z={ground_z:.2f} = {ps.BoundBox.ZMin - ground_z:.2f} mm")
    pin = pillars['L'].Shape.BoundBox.YMin - pillars['R'].Shape.BoundBox.YMax
    L(f"  기둥판 안쪽 간격 = {pin:.2f} mm, 바깥 간격 = {pillars['L'].Shape.BoundBox.YMax - pillars['R'].Shape.BoundBox.YMin:.2f} mm")

    for o in list(doc.Objects):
        if o.TypeId == 'App::DocumentObjectGroup' and not o.Group:
            L(f"  빈 그룹 제거: Name={o.Name} Label={o.Label}")
            doc.removeObject(o.Name)

    note = doc.addObject('App::TextDocument', 'DesignNotes')
    note.Label = '설계메모_v5'
    note.Text = NOTES.format(d=SCREW_CLEAR_D, t=PILLAR_T, g=GUIDE_GAP, h=GUIDE_H, a=GUIDE_ARM, gt=GUIDE_T,
                             bv=BR_LEG_V, bh=BR_LEG_H, bw=BR_W, bt=BR_T, bd=BR_HOLE_D, bx=BR_X)
    doc.recompute()
    bad = [o.Name for o in doc.Objects if 'Invalid' in o.State or 'Error' in o.State]
    L(f"\n  오류 상태 객체: {bad}")

    v = Gui.ActiveDocument.ActiveView
    v.setCameraType('Orthographic')
    v.viewIsometric(); v.fitAll(); Gui.updateGui()
    doc.saveAs(OUT)
    L(f"\n[11] 저장: {OUT} ({os.path.getsize(OUT)} bytes)")
    L('완료')


NOTES = """TeamRobot 밑판 v5 (자동 생성: build_base_v5.py)

[확정 (사용자 지시)]
- 모터: 세움 + 상하 반전, 뒤편(아이들러 쪽) 평면 개조형. XW430 STEP을 XM430 대용으로 사용.
- 모터 뒤편은 기둥판과 나사 고정, 모터 바닥은 밑판과 나사 고정.
- 바퀴 Ø65 일반 바퀴.
- Jetson: 하부 프레임째로, 가이드 블록으로 고정.
- 기둥판과 밑판: L브라켓 + 나사 고정.

[이번에 정한 설계값]
- 나사홀: M2.5 통과 Ø{d} (ISO 273 medium).
- 밑판 구멍 = 모터 바닥면(축 쪽 끝면) Ø2.05 탭 구멍 4개 위치 (STEP 측정).
- 기둥판 구멍 = 모터 케이스 조립 볼트 관통홀 4개 위치 (STEP 측정, 뒷면에 있는 유일한 구멍).
- 기둥판: 두께 {t}, 모터 뒷면에 맞닿도록 배치 (CartRidar 기준 위치에서 바깥으로 이동).
- 가이드 블록: L자 4개, 프레임과 틈새 {g}, 높이 {h}, 팔 길이 {a}, 벽 두께 {gt}.
- L브라켓: 세로 {bv} x 가로 {bh} x 폭 {bw}, 두께 {bt}, 다리마다 M3 Ø{bd} 구멍 1개.
  기둥판 바깥 면(모터 쪽)에 장당 3개, X = {bx}. 기둥판 양 끝은 모터가 밑판·기둥판에 모두 나사 고정되어 있어 생략.

[확인 필요]
1. 기둥판 체결에 케이스 조립 볼트 자리를 쓰는 것이 맞는지 (기존 볼트를 긴 볼트로 교체해야 함).
2. 나사 길이: 모터 바닥 탭 깊이 약 3.0 mm (STEP) -> 밑판 5 mm 기준 나사 길이 8 mm 이하.
3. 가이드 블록과 밑판 고정 방식, 블록만으로는 위로 빠지는 것을 막지 못함 (누름 고정 필요 여부).
4. L브라켓 규격 (규격품 사용 시 치수/구멍 위치), 너트 체결 또는 탭 가공 여부.
5. 바퀴 폭 20 / 허브, 축 X 위치 ±100, 바퀴-밑판 간격 3 mm 는 가정값.
"""

try:
    main()
except Exception:
    L('!!! 오류 발생')
    L(traceback.format_exc())
finally:
    logf.close()
    os._exit(0)
