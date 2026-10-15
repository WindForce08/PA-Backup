# -*- coding: utf-8 -*-
"""TeamRobot 밑판 v2 1단계 조립 모델 생성 스크립트 (FreeCAD 1.1.x, GUI 모드 필요).

실행 (GUI 창 없이):
  FREECAD_USER_HOME=<임시폴더> QT_QPA_PLATFORM=offscreen \
    ~/Application/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage build_base_v2.py

원본(TeamRobot_Base.FCStd, STEP 파일)은 읽기만 하고 저장하지 않는다.
"""
import os, sys, time, traceback
import FreeCAD as App
import FreeCADGui as Gui
import Part
import ImportGui

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_BASE = os.path.join(HERE, '..', 'CAD', 'TeamRobot_Base.FCStd')
DXL_STEP = '/home/pa31/Downloads/XW430.N105.I105.STP'
JET_STEP = '/home/pa31/Downloads/Jetson_Orin_Nano_DevKit_3D_STEP_Model/P3766-P3768SKU4-P3767ENVELOPE.stp'
OUT = os.path.join(HERE, 'TeamRobot_Base_v2_Assembly.FCStd')
LOG = os.path.join(HERE, 'build_base_v2.log')
IMG_DIR = os.environ.get('TR_IMG_DIR', HERE)

PROTECTED = {os.path.realpath(p) for p in (SRC_BASE, DXL_STEP, JET_STEP)}

# ---- 설계 파라미터 (후보 배치용, 확정값 아님) ----
SHAFT_X = 100.0          # 구동축 X 위치 (±). 바퀴 지름 미확인 -> 후보값
MOTOR_MARGIN = 2.0       # 모터 장착 공간 여유
JET_MARGIN = 5.0         # Jetson 측면 여유
JET_AIR_TOP = 15.0       # Jetson 팬 상부 공기 흐름 여유 (가정)
JET_PORT_ACCESS = 30.0   # Jetson I/O 커넥터 플러그 접근 공간 (가정)
JET_PORT_EDGE_X = None   # None이면 밑판 후단 + JET_PORT_ACCESS
PILLAR_Y_IN, PILLAR_Y_OUT, PILLAR_H = 73.5, 78.5, 90.0  # CartRidar.FCStd 측벽 치수를 90° 회전해 적용 (미확정)

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
    """로컬 X/Y/Z 축이 향할 월드 방향으로 회전 생성 (우수 좌표계 검사 포함)."""
    assert abs(xm.cross(ym).sub(zm).Length) < 1e-9, 'not right-handed'
    m = App.Matrix(xm.x, ym.x, zm.x, 0, xm.y, ym.y, zm.y, 0, xm.z, ym.z, zm.z, 0, 0, 0, 0, 1)
    return App.Rotation(m)


def shape_of(o):
    return Part.getShape(o, '', needSubElement=False, transform=True)


def overlap_volume(a, b):
    """두 형상의 솔리드끼리 공통 부피 합 (바운딩 박스로 사전 필터)."""
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


def min_dist(a, b, near=20.0):
    """최소 거리. 바운딩 박스 간격이 near 이상이면 그 값(하한)을 반환하고 정밀 계산은 생략.
    컴파운드 전체에 distToShape를 쓰면 동축 원통 등에서 해가 폭증할 수 있어 솔리드 단위로 계산한다."""
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


def bbox_gap(a, b):
    dx = max(0, max(a.XMin, b.XMin) - min(a.XMax, b.XMax))
    dy = max(0, max(a.YMin, b.YMin) - min(a.YMax, b.YMax))
    dz = max(0, max(a.ZMin, b.ZMin) - min(a.ZMax, b.ZMax))
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def import_step(doc, path):
    # GUI 모드에서 STEP 옵션 대화상자가 뜨면 오프스크린 실행이 멈추므로 끈다
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
    from collections import Counter
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
    nb = App.BoundBox(b.XMin - dx, b.YMin - dy, b.ZMin if zmin is None else zmin,
                      b.XMax + dx, b.YMax + dy, b.ZMax + dz_top)
    return nb


def main():
    L('=== TeamRobot 밑판 v2 (1단계) 생성 ===')
    L('FreeCAD', '.'.join(App.Version()[:3]), App.Version()[3])
    L('시각', time.strftime('%Y-%m-%d %H:%M:%S'))
    if os.path.realpath(OUT) in PROTECTED:
        raise RuntimeError('출력 경로가 원본과 같음')
    L('\n[0] 입력 파일')
    for p in (SRC_BASE, DXL_STEP, JET_STEP):
        if not os.path.isfile(p):
            raise FileNotFoundError(p)
        L(f"  OK {os.path.realpath(p)} ({os.path.getsize(p)} bytes)")

    doc = App.newDocument('TeamRobot_Base_v2')
    doc.Label = 'TeamRobot_Base_v2_Assembly'

    # ---- 1. 기존 밑판 복사 (원본 파일은 저장하지 않음) ----
    L('\n[1] 기존 밑판 복사')
    src = App.openDocument(os.path.realpath(SRC_BASE))
    body_src = src.getObject('Body')
    ref_vol, ref_bb = body_src.Shape.Volume, body_src.Shape.BoundBox
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

    # ---- 2. STEP 원본 가져오기 ----
    L('\n[2] STEP 가져오기 (원본 형상은 수정하지 않고 링크로만 배치)')
    g_src = doc.addObject('App::DocumentObjectGroup', 'STEP_Originals')
    g_src.Label = 'STEP_원본_수정금지(숨김)'
    dxl_root, dxl_new = import_step(doc, DXL_STEP)
    jet_root, jet_new = import_step(doc, JET_STEP)
    g_src.addObject(dxl_root)
    g_src.addObject(jet_root)
    dxl_root.ViewObject.Visibility = False
    jet_root.ViewObject.Visibility = False

    # 로컬 기준값을 형상에서 직접 측정
    dxl_s = shape_of(dxl_root)
    case = [shape_of(o) for o in dxl_new if o.TypeId == 'Part::Feature' and o.Label.startswith('DC12_C04_CASE')]
    case_bb = Part.makeCompound(case).BoundBox
    horn = [shape_of(o) for o in dxl_new if o.Label == 'HN12_N105_DUMMY'][0]
    HORN_Z = horn.BoundBox.ZMax
    L(f"  DXL STEP 전체 : solids={len(dxl_s.Solids)} valid={dxl_s.isValid()} vol={dxl_s.Volume:.1f} {fbb(dxl_s.BoundBox)} plc={fplc(dxl_root.Placement)}")
    L(f"  DXL 케이스    : {fbb(case_bb)}  (출력축 = 로컬 Z, 축 중심 (0,0))")
    L(f"  DXL 혼 바깥면 : 로컬 Z={HORN_Z:.2f}")
    jet_s = shape_of(jet_root)
    jbb = jet_s.BoundBox
    L(f"  Jetson STEP 전체: solids={len(jet_s.Solids)} vol={jet_s.Volume:.1f} {fbb(jbb)} plc={fplc(jet_root.Placement)}")
    pcb = [o for o in jet_new if o.Label == '600-13768-0000-A04'][0]
    L(f"  Jetson 캐리어 PCB: {fbb(shape_of(pcb).BoundBox)}")
    inval = [o.Label for o in dxl_new + jet_new if o.TypeId == 'Part::Feature' and not o.Shape.isNull() and not o.Shape.isValid()]
    L(f"  형상 유효성 실패 객체: {len(inval)} {inval[:10]}")

    # ---- 3. 모터 배치 후보 ----
    X, Y, Z = App.Vector(1, 0, 0), App.Vector(0, 1, 0), App.Vector(0, 0, 1)
    shaft_y = pb.YMax - HORN_Z  # 혼 바깥면을 밑판 가장자리에 맞춤
    corners = [('FL', +1, +1), ('FR', +1, -1), ('RL', -1, +1), ('RR', -1, -1)]

    cands = {}
    # 후보 A: 눕힘 (케이스 측면이 밑판에 닿음, 축 높이 = 상면 + 14.25)
    # 후보 B: 세움 (케이스 끝면(-Y_m)이 밑판에 닿음, 축 높이 = 상면 + 35.25)
    for cname in ('A', 'B'):
        g = doc.addObject('App::DocumentObjectGroup', f'Cand{cname}')
        g.Label = {'A': '후보A_모터_눕힘장착(미확정)', 'B': '후보B_모터_세움장착(미확정)'}[cname]
        items = []
        for tag, sx, sy in corners:
            zm = Y * sy                              # 출력축: 좌우 바깥쪽
            if cname == 'A':
                ym = X * sx                          # 축이 앞/뒤 바깥쪽 끝에 오도록
                xm = ym.cross(zm)
                hz = PLATE_TOP + (-case_bb.XMin if xm.z > 0 else case_bb.XMax)
            else:
                ym = Z                               # 로컬 -Y 끝면이 바닥
                xm = ym.cross(zm)
                hz = PLATE_TOP - case_bb.YMin
            rot = rot_from_axes(xm, ym, zm)
            plc = App.Placement(App.Vector(sx * SHAFT_X, sy * shaft_y, hz), rot)
            lk = doc.addObject('App::Link', f'DXL_{cname}_{tag}')
            lk.LinkedObject = dxl_root
            lk.Placement = plc
            lk.Label = f'DXL_{cname}_{tag} (XW430 STEP)'
            g.addObject(lk)
            # 구동축 표시선 (바퀴 위치 미확인)
            ax = doc.addObject('Part::Line', f'Axis_{cname}_{tag}')
            p0 = plc.multVec(App.Vector(0, 0, case_bb.ZMin))
            p1 = plc.multVec(App.Vector(0, 0, HORN_Z + 40))
            ax.X1, ax.Y1, ax.Z1, ax.X2, ax.Y2, ax.Z2 = p0.x, p0.y, p0.z, p1.x, p1.y, p1.z
            ax.Label = f'구동축_{cname}_{tag}(바퀴 미확정)'
            g.addObject(ax)
            ax.ViewObject.LineColor = (0.9, 0.1, 0.1)
            ax.ViewObject.LineWidth = 3
            items.append((tag, lk, plc))
        cands[cname] = (g, items)

    # ---- 4. Jetson 배치 (I/O 커넥터 변(로컬 -Y)이 후방(-X)을 향하도록 Z축 -90°) ----
        g_j = doc.addObject('App::DocumentObjectGroup', 'Jetson')
    g_j.Label = 'Jetson_OrinNano_예상배치'
    jrot = App.Rotation(Z, -90)
    port_edge_x = (pb.XMin + JET_PORT_ACCESS) if JET_PORT_EDGE_X is None else JET_PORT_EDGE_X
    tx = port_edge_x - jbb.YMin                     # 회전 후 월드 X = 로컬 Y
    ty = (jbb.XMin + jbb.XMax) / 2.0                # 회전 후 월드 Y = -로컬 X -> 중앙 정렬
    tz = PLATE_TOP - jbb.ZMin                       # 하부 프레임 바닥을 밑판 상면에
    jplc = App.Placement(App.Vector(tx, ty, tz), jrot)
    jl = doc.addObject('App::Link', 'Jetson_DevKit')
    jl.LinkedObject = jet_root
    jl.Placement = jplc
    jl.Label = 'Jetson_OrinNano_DevKit (STEP)'
    g_j.addObject(jl)

    # ---- 5. 장착/배치 공간 및 참조 표시 ----
    doc.recompute()
    jw = shape_of(jl)
    jwb = jw.BoundBox
    zone_j = box(doc, 'Zone_Jetson', 'Jetson_배치공간(측면+5, 상부+15 가정)',
                 grow(jwb, JET_MARGIN, JET_MARGIN, JET_AIR_TOP, zmin=PLATE_TOP), g_j, (0.2, 0.75, 0.3))
    zport = App.BoundBox(pb.XMin, jwb.YMin, PLATE_TOP, jwb.XMin, jwb.YMax, jwb.ZMax)
    zone_p = box(doc, 'Zone_JetsonPorts', f'Jetson_IO커넥터_접근공간({JET_PORT_ACCESS:.0f}mm 가정)', zport, g_j, (0.95, 0.85, 0.2))
    for i, (hx, hy) in enumerate([(0, 0), (86, 0), (0, 58), (86, 58)]):
        c = jplc.multVec(App.Vector(hx, hy, 0))
        cy = doc.addObject('Part::Cylinder', f'JetHoleRef{i}')
        cy.Radius, cy.Height = 2.75 / 2, PLATE_TOP - pb.ZMin
        cy.Placement = App.Placement(App.Vector(c.x, c.y, pb.ZMin), App.Rotation())
        cy.Label = f'Jetson_장착구멍_참조{i}(Ø2.75, STEP PCB, 미가공)'
        g_j.addObject(cy)
        cy.ViewObject.ShapeColor = (0.1, 0.5, 0.1)

    for cname, (g, items) in cands.items():
        for tag, lk, plc in items:
            mb = shape_of(lk).BoundBox
            box(doc, f'Zone_{cname}_{tag}', f'모터장착공간_{cname}_{tag}(+{MOTOR_MARGIN:.0f}mm)',
                grow(mb, MOTOR_MARGIN, MOTOR_MARGIN, MOTOR_MARGIN, zmin=PLATE_TOP), g, (1.0, 0.55, 0.1))
            # 밑판에 닿는 케이스 면의 Ø2.05 구멍 위치 (STEP 형상에서 측정한 위치)
            if cname == 'A':
                pts = [(xf, yv, zv) for xf in (case_bb.XMin, case_bb.XMax) for yv in (5.75, -29.75) for zv in (-6, 6)]
            else:
                pts = [(xv, case_bb.YMin, zv) for xv in (-8.75, 8.75) for zv in (-6, 6)]
            k = 0
            for p in pts:
                w = plc.multVec(App.Vector(*p))
                if abs(w.z - PLATE_TOP) > 1e-6:
                    continue
                cy = doc.addObject('Part::Cylinder', f'HoleRef_{cname}_{tag}_{k}')
                cy.Radius, cy.Height = 2.05 / 2, PLATE_TOP - pb.ZMin
                cy.Placement = App.Placement(App.Vector(w.x, w.y, pb.ZMin), App.Rotation())
                cy.Label = f'모터체결구멍_참조_{cname}_{tag}_{k}(Ø2.05 STEP, 미가공)'
                g.addObject(cy)
                cy.ViewObject.ShapeColor = (0.85, 0.1, 0.1)
                k += 1
            assert k == 4, f'{cname}_{tag}: 바닥면 구멍 {k}개'

    g_r = doc.addObject('App::DocumentObjectGroup', 'Reserved')
    g_r.Label = '예약공간_다음단계(미확정)'
    pil = []
    for s in (+1, -1):
        yb = sorted((s * PILLAR_Y_IN, s * PILLAR_Y_OUT))
        pil.append(box(doc, f'Zone_Pillar_{"L" if s > 0 else "R"}',
                       f'기둥판_예약({"좌" if s > 0 else "우"}, CartRidar 측벽 치수 기준)',
                       App.BoundBox(pb.XMin, yb[0], PLATE_TOP, pb.XMax, yb[1], PLATE_TOP + PILLAR_H), g_r, (0.3, 0.45, 0.95), 85))
    zf = App.BoundBox(zone_j.Shape.BoundBox.XMax + 5, -PILLAR_Y_IN + 1, PLATE_TOP, pb.XMax, PILLAR_Y_IN - 1, PLATE_TOP + 40)
    zone_f = box(doc, 'Zone_Front', '전방_예약(OpenCR·TFmini Plus 등, 치수 미입력)', zf, g_r, (0.55, 0.3, 0.9), 85)

    doc.recompute()

    # ---- 6. 로그: 배치/바운딩박스/유효성 ----
    L('\n[3] 배치 결과: 모터 (출력축 = 로컬 Z, 혼 바깥면을 밑판 가장자리 Y=±%.1f에 맞춤)' % pb.YMax)
    for cname, (g, items) in cands.items():
        L(f"  -- 후보 {cname}: {g.Label}")
        for tag, lk, plc in items:
            s = shape_of(lk)
            r = plc.Rotation
            L(f"   {lk.Name}: {fplc(plc)}  로컬X->{tuple(round(v) for v in r.multVec(X))} 로컬Y->{tuple(round(v) for v in r.multVec(Y))} 로컬Z(축)->{tuple(round(v) for v in r.multVec(Z))}")
            L(f"      valid={s.isValid()} solids={len(s.Solids)} {fbb(s.BoundBox)}")
    L(f"  Jetson: {fplc(jplc)}  valid={jw.isValid()} solids={len(jw.Solids)} {fbb(jwb)}")
    L(f"  밑판   : {fbb(pb)}")
    for z in (zone_j, zone_p, zone_f, *pil):
        L(f"  공간 {z.Label}: {fbb(z.Shape.BoundBox)}")

    # ---- 7. 간섭 검사 ----
    L('\n[4] 간섭 검사 (공통 부피 > 0.001 mm³ 이면 간섭)')
    TH = 1e-3
    for cname, (g, items) in cands.items():
        L(f"  -- 후보 {cname}")
        shp = {tag: shape_of(lk) for tag, lk, _ in items}
        for tag, s in shp.items():
            v = overlap_volume(s, ps)
            d = min_dist(s, ps)[0]
            out = max(0, s.BoundBox.YMax - pb.YMax, pb.YMin - s.BoundBox.YMin)
            L(f"   {tag} x 밑판   : 공통={v:.4f} mm³ {'간섭' if v > TH else 'OK'}  최소거리={d:.3f} (0=접촉)  밑판 밖 돌출(Y)={out:.2f}")
        tags = list(shp)
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                a, b = shp[tags[i]], shp[tags[j]]
                v = overlap_volume(a, b)
                d, how = min_dist(a, b)
                L(f"   {tags[i]} x {tags[j]}    : 공통={v:.4f} {'간섭' if v > TH else 'OK'}  최소거리={d:.2f} ({how})")
        for tag, s in shp.items():
            v = overlap_volume(s, jw)
            d, how = min_dist(s, jw)
            L(f"   {tag} x Jetson : 공통={v:.4f} {'간섭' if v > TH else 'OK'}  최소거리={d:.2f} ({how}; bbox는 하한값)")
        for tag, s in shp.items():
            for z in (zone_j, zone_p, zone_f, *pil):
                v = overlap_volume(s, z.Shape)
                if v > TH:
                    L(f"   [주의] {tag} 모터 형상이 {z.Label} 과 겹침: {v:.1f} mm³")
            for z in pil:
                d, how = min_dist(s, z.Shape)
                L(f"   {tag} x {z.Label}: 최소거리={d:.2f} mm ({how})")
    v = overlap_volume(jw, ps)
    L(f"  Jetson x 밑판: 공통={v:.4f} {'간섭' if v > TH else 'OK'}  최소거리={min_dist(jw, ps)[0]:.3f}")
    for z in pil + [zone_f]:
        L(f"  Jetson 배치공간 x {z.Label}: 공통={overlap_volume(zone_j.Shape, z.Shape):.1f} mm³")

    # 내용이 없는 그룹(가져오기 과정 등에서 생긴 것) 정리
    for o in list(doc.Objects):
        if o.TypeId == 'App::DocumentObjectGroup' and not o.Group:
            L(f"  빈 그룹 제거: Name={o.Name} Label={o.Label} InList={[i.Name for i in o.InList]}")
            doc.removeObject(o.Name)

    # ---- 8. 설계 메모 ----
    note = doc.addObject('App::TextDocument', 'DesignNotes')
    note.Label = '설계메모_미확정사항'
    note.Text = NOTES
    doc.recompute()

    # ---- 9. 화면/저장 ----
    for cn in ('B',):
        for o in cands[cn][0].Group:
            o.ViewObject.Visibility = False
        cands[cn][0].ViewObject.Visibility = False
    v = Gui.ActiveDocument.ActiveView
    v.setCameraType('Orthographic')
    for nm, fn in (('iso', v.viewIsometric), ('top', v.viewTop), ('front', v.viewFront)):
        fn(); v.fitAll(); Gui.updateGui()
        v.saveImage(os.path.join(IMG_DIR, f'base_v2_candA_{nm}.png'), 1600, 1200, 'White')
    for o in cands['A'][0].Group:
        o.ViewObject.Visibility = False
    for o in cands['B'][0].Group:
        o.ViewObject.Visibility = True
    cands['B'][0].ViewObject.Visibility = True
    v.viewIsometric(); v.fitAll(); Gui.updateGui()
    v.saveImage(os.path.join(IMG_DIR, 'base_v2_candB_iso.png'), 1600, 1200, 'White')
    for o in cands['B'][0].Group:
        o.ViewObject.Visibility = False
    cands['B'][0].ViewObject.Visibility = False
    for o in cands['A'][0].Group:
        o.ViewObject.Visibility = True
    v.viewIsometric(); v.fitAll()
    doc.saveAs(OUT)
    L(f"\n[5] 저장: {OUT} ({os.path.getsize(OUT)} bytes)")
    L('완료')


NOTES = """TeamRobot 밑판 v2 - 1단계 (자동 생성: build_base_v2.py)

[원본]
- 밑판: TeamRobot/CAD/TeamRobot_Base.FCStd 의 Body(270x250x5)를 그대로 복사. 원본 파일은 저장하지 않음.
- 모터 STEP: ~/Downloads/XW430.N105.I105.STP
  * 파일명/부품명상 XW430(방수형, WEIPU 커넥터·씰 포함) 모델이며 XM430-W210 STEP이 아님.
  * 케이스 외형 28.5 x 46.5 x 34.0 mm, 출력축 = 로컬 Z, 혼은 +Z.
  * 케이스 측면/끝면에 Ø2.05 막힌 구멍 모델링됨(나사 규격 정보 없음).
  * HN12_I105, IGUS_GSM_1517_04 는 케이스 내부 원점에 겹쳐 있음(미배치 더미로 보임).
- Jetson STEP: ~/Downloads/Jetson_Orin_Nano_DevKit_3D_STEP_Model/P3766-P3768SKU4-P3767ENVELOPE.stp
  * 개발 키트 전체: 캐리어 PCB(600-13768, 100x79x1.57) + 모듈(P3767) + 방열판/팬 + Wi-Fi/NVMe + 하부 프레임(375-0137).
  * 캐리어 PCB에 Ø2.75 관통홀이 (0,0)(86,0)(0,58)(86,58) 외 다수 모델링됨.

[미확정]
1. 모터 방향/배치: 바퀴·구동축 구조 미확인 -> 후보 A(눕힘), B(세움) 모두 미확정.
2. 바퀴 지름, 지상고, 축 X 위치(현재 ±100 가정).
3. XM430-W210 실물과 XW430 STEP의 체결구멍/커넥터 위치 일치 여부.
4. 모터 체결 나사 규격, 밑판 관통홀 지름 -> 구멍은 '참조 표시'만 하고 밑판에 가공하지 않음.
5. Jetson 고정 방식(하부 프레임째 고정 vs 프레임 제거 후 스탠드오프) 및 높이.
6. 기둥판 위치는 CartRidar.FCStd 측벽(두께 5, 내측 간격 147, 높이 90)을 90° 회전해 가정.
7. 로봇 전방 = +X 로 가정.
"""

try:
    main()
except Exception:
    L('!!! 오류 발생')
    L(traceback.format_exc())
finally:
    logf.close()
    os._exit(0)
