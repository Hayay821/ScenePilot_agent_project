import yaml

files = [
    'skills/repository/builtin/director/portrait_story_director.yaml',
    'skills/repository/builtin/cinematographer/portrait_composition_coach.yaml',
    'skills/repository/builtin/editor/portrait_reel_editor.yaml'
]

all_actions = set()
for f in files:
    data = yaml.safe_load(open(f, encoding='utf-8'))
    safety = data.get('safety', {})
    all_actions.update(safety.get('allowed_actions', []))
    all_actions.update(safety.get('requires_human_approval', []))

for action in sorted(all_actions):
    print(action)
