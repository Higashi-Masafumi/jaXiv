import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { Input } from './input'

const meta = {
  component: Input,
  title: 'UI/Input',
  tags: ['autodocs'],
  args: {
    onChange: fn(),
    onFocus: fn(),
    onBlur: fn(),
  },
} satisfies Meta<typeof Input>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    placeholder: 'Enter text...',
  },
}

export const WithValue: Story = {
  args: {
    value: 'Sample text',
    placeholder: 'Enter text...',
  },
}

export const WithPlaceholder: Story = {
  args: {
    placeholder: '例: 2006.08131',
  },
}

export const Disabled: Story = {
  args: {
    placeholder: 'Enter text...',
    disabled: true,
  },
}

export const Error: Story = {
  args: {
    placeholder: 'Enter text...',
    'aria-invalid': true,
    defaultValue: 'Invalid input',
  },
}

export const TypeEmail: Story = {
  args: {
    type: 'email',
    placeholder: 'email@example.com',
  },
}

export const TypePassword: Story = {
  args: {
    type: 'password',
    placeholder: 'Enter password...',
  },
}

export const TypeNumber: Story = {
  args: {
    type: 'number',
    placeholder: 'Enter number...',
  },
}
