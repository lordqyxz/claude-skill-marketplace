import shutil
import sys
from pathlib import Path


def install():
    src = Path(__file__).parent / "skills"
    dst = Path.home() / ".claude" / "skills"

    if not src.exists():
        print("Error: skills directory not found in package", file=sys.stderr)
        sys.exit(1)

    dst.mkdir(parents=True, exist_ok=True)

    for skill_name in ["skill-creator", "python-code", "python-developer", "vue3-sfc"]:
        skill_src = src / skill_name
        skill_dst = dst / skill_name

        if skill_src.exists():
            if skill_dst.exists():
                shutil.rmtree(skill_dst)
            shutil.copytree(skill_src, skill_dst)
            print(f"Installed skill: {skill_name}")
        else:
            print(f"Warning: skill '{skill_name}' not found in package", file=sys.stderr)

    print("\nTo enable skills, add to ~/.claude/settings.json:")
    print('  "skills": { "skill-creator": true, "python-code": true, "python-developer": true, "vue3-sfc": true }')


if __name__ == "__main__":
    install()
