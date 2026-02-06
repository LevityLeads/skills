# LevityLeads Skills Library

Reusable Claude Skills for building products fast. These are battle-tested patterns from real projects.

## What Are Skills?

Skills are instruction files that teach Claude how to perform tasks in a repeatable way. When a task matches a skill's description, Claude reads the SKILL.md and follows the patterns.

## Available Skills

| Skill | Description |
|-------|-------------|
| [gmail-proxy](./gmail-proxy/) | Gmail/Calendar integration via REST proxy (no OAuth in frontend) |
| [infinite-canvas](./infinite-canvas/) | React Flow nested canvas with navigation |
| [glassmorphism-ui](./glassmorphism-ui/) | Modern glassmorphism styling with Tailwind |
| [nextjs-api](./nextjs-api/) | Next.js API route patterns and best practices |
| [railway-deploy](./railway-deploy/) | Deploy Node.js services to Railway |
| [vercel-deploy](./vercel-deploy/) | Deploy Next.js apps to Vercel |

## Installation

### For OpenClaw
Clone into your workspace:
```bash
git clone https://github.com/LevityLeads/skills /data/workspace/skills
```

### For Claude Code CLI
```bash
/plugin add /path/to/skills/skill-name
```

## Skill Structure

Each skill follows this structure:
```
skill-name/
├── SKILL.md          # Main instructions (keep under 500 lines)
├── examples/         # Code examples
├── templates/        # Starter templates
└── scripts/          # Helper scripts (optional)
```

## Contributing

1. Create a new folder for your skill
2. Add a SKILL.md with clear instructions
3. Include examples where helpful
4. Keep SKILL.md focused - put detailed docs in separate files

## License

MIT - Use these however you want.
