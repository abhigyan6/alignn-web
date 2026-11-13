# emilkowalski/skills: use-case guide

Installed in `.claude/skills/` (19 skills, instruction files only, no bundled scripts).
Source: https://github.com/emilkowalski/skills. Summary is from each skill's frontmatter; full SKILL.md bodies were not reviewed.

Per `AGENTS.md`, do not auto-invoke skill collections. Use a skill only when a task asks for it.

## Fits Alignn (Next.js marketplace web app)

| Skill | Use it for | Runs |
|---|---|---|
| `animate` | Building a new animation or transition: whether to animate, curve, duration, interruption, exit | Automatically |
| `choreograph` | Several elements animating together: staggered lists, hero entrances, view swaps | Automatically |
| `gestures` | Drag, swipe and sheet interactions: drawers, swipe-to-dismiss, reorder, pull-to-refresh | Automatically |
| `animation-performance` | Janky or choppy animation, CSS vs JS, when `will-change` helps | Automatically |
| `mobile-native` | Making the web app feel native on phones: 100vh bug, input zoom, tap flashes, notch, PWA | Automatically |
| `ask-sonner` | Wiring up or debugging the Sonner toast library | Automatically |
| `apple-design` | Apple-style interaction design: springs, momentum, materials, typography, reduced motion | Automatically |
| `emil-design-eng` | General UI polish and component-design philosophy | Automatically |
| `break-ui` | Stress-testing a component with worst-case data, behind a "Worst case" toggle | Automatically |
| `animation-vocabulary` | Turning a vague motion description into the right term | Automatically |
| `find-animation-opportunities` | Read-only: finds places that should animate, proposes exact values | Automatically |
| `improve-animations` | Read-only: audits existing motion and writes implementation plans | Automatically |
| `remove-animations` | Strips unneeded motion when the app feels slow or over-animated; only deletes | Automatically |
| `review-animations` | Strict review of motion code ("default to flagging") | Only when invoked |
| `learn-taste` | Turns design corrections into rules in `DESIGN.md` or a project skill | Only when invoked |
| `pick-ui-library` | Picks libraries for charts, OTP inputs, command menus, virtualization, etc. | Only when invoked |
| `prototype` | Builds several different versions of a UI piece behind a picker | Only when invoked |

## Not relevant to this project
- `animate-expo`: React Native and Expo animation.
- `write-swift`: modern Swift, concurrency and testing.

## Caveats
- Several skills assume libraries (Motion/Framer Motion, Vaul, Sonner) that Alignn may not use. Check the codebase first.
- `prototype` and `break-ui` add temporary UI (picker, "Worst case" toggle). Keep that out of production code, in line with the rule against shipping concept controls as working features.
