"""
ik_measurement_points.py
========================
Helper script for visual measurement of the IK Tool end-effector position.

Creates two reference points in the FreeCAD viewport:
    - Origin_IK_Point (green):  always at (0, 0, 0) — document origin
    - EF_IK_Point     (red):    current EF position in world frame

Usage (FreeCAD Python console):
    IK_MEASURE = '/home/alejandro/robotcad_clean/freecad/cross/ui/command_ik_measurement_points.py'
    exec(open(IK_MEASURE).read())

Or with a specific end-effector label:
    EE_LABEL = 'l_palm003'
    exec(open(IK_MEASURE).read())
"""

import math
import importlib

import numpy as np
import Part
import FreeCAD as fc

# ── imports from RobotCAD/RobotTool ──────────────────────────────────────────
import freecad.cross.kinematics.kinematics as _fk_mod
import freecad.cross.ui.command_ik_tool as _ik_cmd

importlib.reload(_fk_mod)
importlib.reload(_ik_cmd)

from freecad.cross.kinematics.kinematics import compute_forward_kinematics_full
from freecad.cross.ui.command_ik_tool import (
    _build_parent_map,
    _get_chain_to_root,
    _build_robot_for_chain,
    _get_robot_global_transform,
    _read_joint_positions,
)

# ── configuration ─────────────────────────────────────────────────────────────
if 'EE_LABEL' not in dir():
    EE_LABEL = 'l_palm003'

ORIGIN_NAME = 'Origin_IK_Point'
EF_NAME     = 'EF_IK_Point'

# ── setup ─────────────────────────────────────────────────────────────────────
doc = fc.activeDocument()
if doc is None:
    raise RuntimeError("No active FreeCAD document.")

robot_obj = next(
    (o for o in doc.Objects
        if hasattr(o, 'Proxy') and 'Robot' in type(o.Proxy).__name__),
    None,
)
if robot_obj is None:
    raise RuntimeError("No Cross::Robot object found in the document.")

child_to_parent, child_to_joint = _build_parent_map(robot_obj)
chain = _get_chain_to_root(
    robot_obj, EE_LABEL, child_to_parent, child_to_joint
)
if not chain:
    raise RuntimeError(f"No kinematic chain found to '{EE_LABEL}'.")

robot_model = _build_robot_for_chain(robot_obj, chain)
T_world     = _get_robot_global_transform(robot_obj)

# ── compute current EF position ───────────────────────────────────────────────
q      = _read_joint_positions(chain, robot_obj)
all_T  = compute_forward_kinematics_full(robot_model, q)
pos    = (T_world @ all_T[-1])[:3, 3]

# Cross-check against FreeCAD placement
link_ef = robot_obj.getObject(EE_LABEL)
if link_ef is not None:
    pos_fc = link_ef.Placement.Base
    diff = math.sqrt(
        (pos[0] - pos_fc.x) ** 2 +
        (pos[1] - pos_fc.y) ** 2 +
        (pos[2] - pos_fc.z) ** 2
    )
    if diff > 0.1:
        print(f"[WARNING] FK vs FreeCAD diff = {diff:.4f} mm")
        print(f"  Solver: ({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
        print(f"  FreeCAD: ({pos_fc.x:.3f}, {pos_fc.y:.3f}, {pos_fc.z:.3f})")
        print(f"  Using FreeCAD placement as ground truth.")
        # Use FreeCAD placement as it reflects the actual rendered position
        pos = np.array([pos_fc.x, pos_fc.y, pos_fc.z])
    else:
        print(f"[OK] FK matches FreeCAD placement (diff={diff:.4f} mm)")

# ── remove old points ─────────────────────────────────────────────────────────
for name in (ORIGIN_NAME, EF_NAME):
    existing = doc.getObject(name)
    if existing is not None:
        doc.removeObject(existing.Name)

# ── create origin point (green) ───────────────────────────────────────────────
orig = doc.addObject('Part::Feature', ORIGIN_NAME)
orig.Shape = Part.Vertex(fc.Vector(0.0, 0.0, 0.0))
if hasattr(orig, 'ViewObject'):
    orig.ViewObject.PointSize  = 15
    orig.ViewObject.PointColor = (0.0, 1.0, 0.0)
orig.Label = ORIGIN_NAME

# ── create EF point (red) ─────────────────────────────────────────────────────
ef_pt = doc.addObject('Part::Feature', EF_NAME)
ef_pt.Shape = Part.Vertex(fc.Vector(float(pos[0]), float(pos[1]), float(pos[2])))
if hasattr(ef_pt, 'ViewObject'):
    ef_pt.ViewObject.PointSize  = 15
    ef_pt.ViewObject.PointColor = (1.0, 0.0, 0.0)
ef_pt.Label = EF_NAME

doc.recompute()

# ── joints summary ────────────────────────────────────────────────────────────
print("=" * 55)
print(f"IK Measurement Points — EF: {EE_LABEL}")
print("=" * 55)
print(f"  🟢 {ORIGIN_NAME:<20s}:  X=  0.000  Y=  0.000  Z=  0.000 mm")
print(f"  🔴 {EF_NAME:<20s}:  X={pos[0]:7.3f}  Y={pos[1]:7.3f}  Z={pos[2]:7.3f} mm")
print()
print("Joints (current):")
jvars = robot_obj.Proxy.joint_variables
for j, prop in jvars.items():
    deg = getattr(robot_obj, prop)
    rad = j.Position
    print(f"  {j.Label:<40s}  {deg:+8.3f}°  ({rad:+.4f} rad)")
print()
r = math.sqrt(float(pos[0])**2 + float(pos[1])**2)
print(f"Radial distance from Z axis: {r:.3f} mm (nominal: 48.000 mm)")
print()
print("→ Use Part → Measure Linear:")
print("    Select green point → red point")
print(f"    Expected:  X={pos[0]:.3f}  Y={pos[1]:.3f}  Z={pos[2]:.3f} mm")
print("=" * 55)