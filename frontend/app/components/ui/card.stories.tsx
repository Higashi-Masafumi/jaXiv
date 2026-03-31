import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { Button } from './button'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from './card'

const meta = {
  component: Card,
  title: 'UI/Card',
  tags: ['autodocs'],
} satisfies Meta<typeof Card>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: args => (
    <Card {...args} className="w-full max-w-md">
      <CardHeader>
        <CardTitle>カードのタイトル</CardTitle>
        <CardDescription>
          補足や説明文をここに置きます。リストやフォームの枠として使えます。
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          メイン領域のコンテンツです。
        </p>
      </CardContent>
      <CardFooter className="gap-2">
        <Button variant="outline" size="sm" onClick={fn()}>
          キャンセル
        </Button>
        <Button size="sm" onClick={fn()}>
          保存
        </Button>
      </CardFooter>
    </Card>
  ),
}

export const WithHeaderAction: Story = {
  render: args => (
    <Card {...args} className="w-full max-w-md">
      <CardHeader>
        <CardTitle>ヘッダーにアクション</CardTitle>
        <CardDescription>
          CardAction で見出し行の右側にボタンなどを置けます。
        </CardDescription>
        <CardAction>
          <Button variant="ghost" size="sm" onClick={fn()}>
            編集
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">本文コンテンツ</p>
      </CardContent>
    </Card>
  ),
}

export const HeaderAndContentOnly: Story = {
  render: args => (
    <Card {...args} className="w-full max-w-md">
      <CardHeader>
        <CardTitle>フッターなし</CardTitle>
        <CardDescription>
          ヘッダーとコンテンツだけの最小構成です。
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">CardFooter を省略した例です。</p>
      </CardContent>
    </Card>
  ),
}

export const ShadowNone: Story = {
  name: 'Shadow none (flat)',
  render: args => (
    <Card {...args} className="w-full max-w-md shadow-none">
      <CardHeader>
        <CardTitle>フラットなカード</CardTitle>
        <CardDescription>
          一覧のタイルなどで shadow を消すときの例です。
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          className に shadow-none
        </p>
      </CardContent>
    </Card>
  ),
}
