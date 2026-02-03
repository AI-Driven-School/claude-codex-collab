import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'StressAgent Pro',
  description: 'AI駆動型メンタルヘルスSaaS',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  )
}
