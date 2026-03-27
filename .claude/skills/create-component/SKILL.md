---
name: create-component
description: Create a new React component with Storybook story following this project's conventions (shadcn/ui style, Tailwind CSS, CVA, CSF 3.0). Use when asked to create a new UI component, add a component to the design system, or generate a component with its story.
argument-hint: [ComponentName]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Create Component with Storybook Story

Create a new React component and its Storybook story file for the jaxiv project.

## Arguments

- `$0`: Component name in PascalCase (e.g., `Card`, `Badge`, `Tooltip`)

If the user provides additional context about the component's purpose, variants, or behavior, incorporate that into the implementation.

## File Locations

- Component: `frontend/app/components/ui/{kebab-case-name}.tsx`
- Story: `frontend/app/components/ui/{kebab-case-name}.stories.tsx`

Convert the PascalCase component name to kebab-case for file names (e.g., `SearchBar` -> `search-bar.tsx`).

## Step 1: Research

Before writing code:

1. Check if the component already exists in `frontend/app/components/ui/`
2. Read existing components (button.tsx, input.tsx) to stay consistent with the current patterns
3. If the component exists in shadcn/ui, consider using `npx shadcn@latest add {component}` first, then adjust if needed

## Step 2: Create the Component

Follow these exact conventions from the existing codebase:

### Code Style (Prettier config)
- No semicolons
- Single quotes
- Trailing commas on all
- Arrow parens: avoid

### Component Pattern

```tsx
import * as React from 'react'
// Import cva and VariantProps only if the component needs variants
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '~/lib/utils'

// If the component has variants, define them with cva
const {componentName}Variants = cva(
  'base-classes-here',
  {
    variants: {
      variant: {
        default: '...',
        // other variants
      },
      size: {
        default: '...',
        // other sizes
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

// Use function declaration (not arrow function)
// Extend native HTML element props with React.ComponentProps<'element'>
function ComponentName({
  className,
  variant,
  size,
  ...props
}: React.ComponentProps<'div'> &
  VariantProps<typeof {componentName}Variants>) {
  return (
    <div
      data-slot="{component-name}"
      className={cn({componentName}Variants({ variant, size, className }))}
      {...props}
    />
  )
}

export { ComponentName, {componentName}Variants }
```

### Key Rules
- Use `function` declarations, NOT arrow functions or `forwardRef`
- Use `React.ComponentProps<'element'>` for prop types
- Add `data-slot="{kebab-case-name}"` attribute to the root element
- Use `cn()` from `~/lib/utils` for className merging
- Use named exports (NOT default exports)
- Only use CVA if the component genuinely needs variants; simple components can just use `cn()`
- Use Tailwind CSS classes that align with the project's design tokens (CSS variables like `bg-primary`, `text-muted-foreground`, etc.)

## Step 3: Create the Storybook Story

Follow the existing CSF 3.0 pattern exactly:

```tsx
import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { ComponentName } from './{kebab-case-name}'

const meta = {
  component: ComponentName,
  title: 'UI/ComponentName',
  tags: ['autodocs'],
  args: {
    // Add fn() for event handler props (onClick, onChange, etc.)
  },
} satisfies Meta<typeof ComponentName>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    // default props
  },
}

// Add stories for each variant
export const VariantName: Story = {
  args: {
    variant: 'variant-name',
    // other props
  },
}
```

### Story Rules
- Import Meta and StoryObj from `@storybook/react-vite` (NOT `@storybook/react`)
- Import `fn` from `storybook/test` for event handler mocks
- Use `satisfies Meta<typeof Component>` (NOT `: Meta<typeof Component>`)
- Title format: `'UI/ComponentName'`
- Always include `tags: ['autodocs']`
- Export story variants using PascalCase names
- Create stories covering: Default state, each variant, each size, interactive states (disabled, error, etc.), and usage examples with children/content
- Do NOT import `fn` if the component has no event handler args

## Step 4: Verify

After creating the files:

1. Run `cd frontend && npx tsc --noEmit` to check for type errors
2. Confirm the story file matches the glob pattern: `app/components/**/*.stories.@(js|jsx|ts|tsx|mdx)`

## Output

After completion, summarize:
- Files created
- Component variants/props available
- How to view in Storybook: `cd frontend && npm run storybook`
