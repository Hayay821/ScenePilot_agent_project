"""
Command-line interface for agent module
"""

import argparse
import sys
from pathlib import Path
import json

from agents_Module.skills import SkillRepository, SkillValidator
from agents_Module.orchestration import AgentOrchestrator
from agents_Module.providers import MockProvider


def cmd_list_skills(args):
    """List available skills"""
    repo = SkillRepository(args.skill_dir)

    if args.query:
        skills = repo.search(query=args.query, max_results=args.limit)
    elif args.tags:
        tags = args.tags.split(',')
        skills = repo.search(tags=tags, max_results=args.limit)
    else:
        skills = repo.list_all()[:args.limit]

    print(f"\nFound {len(skills)} skills:\n")

    for skill in skills:
        print(f"📦 {skill.name} ({skill.skill_id})")
        print(f"   Version: {skill.version} | Status: {skill.status.value}")
        print(f"   {skill.description[:80]}...")
        print(f"   Tags: {', '.join(skill.tags[:5])}")
        print()


def cmd_validate_skill(args):
    """Validate a skill"""
    repo = SkillRepository(args.skill_dir)
    validator = SkillValidator()

    skill = repo.load_skill(args.skill_id, version=args.version)

    if not skill:
        print(f"❌ Skill '{args.skill_id}' not found")
        return 1

    print(f"\nValidating: {skill.name} (v{skill.version})\n")

    is_valid, errors = validator.validate(skill)

    if is_valid:
        print("✅ Validation passed!")
        return 0
    else:
        print("❌ Validation failed:\n")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        return 1


def cmd_run_workflow(args):
    """Run complete workflow"""
    repo = SkillRepository(args.skill_dir)
    validator = SkillValidator()
    provider = MockProvider() if args.mock else None

    orchestrator = AgentOrchestrator(
        skill_repository=repo,
        skill_validator=validator,
        model_provider=provider,
        audit_log_path=args.audit_log
    )

    print(f"\n🎬 Running workflow: {args.user_input}\n")

    # Parse devices
    devices = args.devices.split(',') if args.devices else ["link2", "x4air"]

    # Run workflow
    results = orchestrator.run_complete_workflow(
        user_input=args.user_input,
        available_devices=devices,
        user_level=args.user_level,
        events=[],
        media_sources=[]
    )

    # Display results
    print("\n" + "="*60)
    print("WORKFLOW RESULTS")
    print("="*60)

    for step_name, result in results.items():
        if result.is_successful():
            print(f"\n✅ {step_name.upper()}")

            if args.verbose:
                print(f"   Confidence: {result.confidence:.2f}")
                if result.teaching_notes:
                    print(f"   Teaching Notes:")
                    for note in result.teaching_notes:
                        print(f"     • {note}")
        else:
            print(f"\n❌ {step_name.upper()} - Failed")
            if result.errors:
                for error in result.errors:
                    print(f"     ❌ {error}")

    # Save output if requested
    if args.output:
        output_path = Path(args.output)
        output_data = {
            step: result.output
            for step, result in results.items()
            if result.is_successful()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Results saved to: {output_path}")

    print("\n" + "="*60)

    return 0


def cmd_info(args):
    """Show skill details"""
    repo = SkillRepository(args.skill_dir)

    skill = repo.load_skill(args.skill_id, version=args.version)

    if not skill:
        print(f"❌ Skill '{args.skill_id}' not found")
        return 1

    print("\n" + "="*60)
    print(f"SKILL: {skill.name}")
    print("="*60)

    print(f"\nID: {skill.skill_id}")
    print(f"Version: {skill.version}")
    print(f"Status: {skill.status.value}")
    print(f"Visibility: {skill.visibility.value}")
    print(f"License: {skill.license}")

    print(f"\nAuthor:")
    print(f"  {skill.author.display_name} ({skill.author.type.value})")
    print(f"  Verified: {'✓' if skill.author.verified else '✗'}")

    print(f"\nDescription:")
    print(f"  {skill.description}")

    print(f"\nTeaching:")
    print(f"  Audience: {skill.teaching.audience}")
    print(f"  Principles:")
    for principle in skill.teaching.principles:
        print(f"    • {principle}")

    print(f"\nAgent Bindings:")
    bindings = skill.agent_bindings.model_dump()
    for agent, enabled in bindings.items():
        if enabled:
            print(f"  ✓ {agent}")

    print(f"\nRules ({len(skill.rules)}):")
    for rule in skill.rules:
        print(f"  • {rule.id} (priority: {rule.priority})")
        print(f"    When: {rule.when.event} @ {rule.when.confidence_gte:.2f}")
        print(f"    Advice: {rule.advice.model_dump(exclude_none=True)}")
        print(f"    → {rule.explanation}")

    print(f"\nSafety:")
    print(f"  Allowed Actions: {', '.join(skill.safety.allowed_actions[:5])}")
    print(f"  Min Confidence: {skill.safety.min_confidence_for_device_suggestion}")

    print(f"\nTags:")
    print(f"  {', '.join(skill.tags)}")

    print("\n" + "="*60)

    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ScenePilot Agent Module CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all skills
  python -m agents_Module.cli list

  # Search skills by tag
  python -m agents_Module.cli list --tags "动作摄影"

  # Show skill details
  python -m agents_Module.cli info action_coach

  # Validate skill
  python -m agents_Module.cli validate action_coach

  # Run workflow
  python -m agents_Module.cli run "拍摄动作视频" --devices link2,x4air
        """
    )

    parser.add_argument(
        '--skill-dir',
        default='./skills/local_skills',
        help='Path to skill repository (default: ./skills/local_skills)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List available skills')
    list_parser.add_argument('--query', help='Text search query')
    list_parser.add_argument('--tags', help='Comma-separated tags')
    list_parser.add_argument('--limit', type=int, default=10, help='Max results')
    list_parser.set_defaults(func=cmd_list_skills)

    # Info command
    info_parser = subparsers.add_parser('info', help='Show skill details')
    info_parser.add_argument('skill_id', help='Skill ID')
    info_parser.add_argument('--version', help='Specific version')
    info_parser.set_defaults(func=cmd_info)

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a skill')
    validate_parser.add_argument('skill_id', help='Skill ID')
    validate_parser.add_argument('--version', help='Specific version')
    validate_parser.set_defaults(func=cmd_validate_skill)

    # Run command
    run_parser = subparsers.add_parser('run', help='Run workflow')
    run_parser.add_argument('user_input', help='User description of what to film')
    run_parser.add_argument('--devices', default='link2,x4air', help='Available devices')
    run_parser.add_argument('--user-level', default='beginner', choices=['beginner', 'intermediate', 'advanced'])
    run_parser.add_argument('--mock', action='store_true', help='Use mock provider')
    run_parser.add_argument('--output', help='Save results to JSON file')
    run_parser.add_argument('--audit-log', help='Audit log file path')
    run_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    run_parser.set_defaults(func=cmd_run_workflow)

    # Parse and execute
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
