import { useCallback, useRef, useState } from 'react'
import { client } from '~/api/client.gen'
import { getAuthToken } from '~/api/core/auth.gen'
import { createSseClient } from '~/api/core/serverSentEvents.gen'
import type { HttpMethod } from '~/api/core/types.gen'

type BlogChunk =
  | { type: 'intermediate'; message: string }
  | { type: 'complete'; message: string; paper_id: string }
  | { type: 'error'; message: string; error_details: string }

export type BlogStreamStep = { message: string; done: boolean }
export type BlogStreamStatus = 'idle' | 'streaming' | 'complete' | 'error'

export function useBlogStream() {
  const [status, setStatus] = useState<BlogStreamStatus>('idle')
  const [steps, setSteps] = useState<BlogStreamStep[]>([])
  const [error, setError] = useState<string | null>(null)
  const [paperId, setPaperId] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const consume = useCallback(
    async (url: string, method: Uppercase<HttpMethod>, body?: BodyInit) => {
      abortRef.current?.abort()
      const ac = new AbortController()
      abortRef.current = ac

      setStatus('streaming')
      setSteps([])
      setError(null)
      setPaperId(null)

      const { stream } = createSseClient({
        url,
        method,
        onRequest: async (_url, init) => {
          const config = client.getConfig()
          if (config.auth) {
            const token = await getAuthToken(
              { type: 'http', scheme: 'bearer' },
              config.auth,
            )
            const headers = new Headers(
              init.headers as Record<string, string> | undefined,
            )
            if (token) headers.set('Authorization', token)
            return new Request(_url, { ...init, headers })
          }
          return new Request(_url, init)
        },
        ...(body !== undefined && { serializedBody: body }),
        signal: ac.signal,
        sseMaxRetryAttempts: 0,
      })

      for await (const raw of stream) {
        if (ac.signal.aborted) break
        const chunk = raw as BlogChunk
        if (chunk.type === 'intermediate') {
          setSteps(prev => {
            const updated = prev.map((s, i) =>
              i === prev.length - 1 ? { ...s, done: true } : s,
            )
            return [...updated, { message: chunk.message, done: false }]
          })
        } else if (chunk.type === 'complete') {
          setSteps(prev => prev.map(s => ({ ...s, done: true })))
          setPaperId(chunk.paper_id)
          setStatus('complete')
          return
        } else if (chunk.type === 'error') {
          setError(chunk.error_details ?? chunk.message)
          setStatus('error')
          return
        }
      }
    },
    [],
  )

  const startArxivStream = useCallback(
    (arxivPaperId: string) => {
      consume(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/blog/arxiv/${arxivPaperId}/stream`,
        'GET',
      )
    },
    [consume],
  )

  const startPdfStream = useCallback(
    (file: File) => {
      const body = new FormData()
      body.append('file', file)
      consume(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/blog/pdf/stream`,
        'POST',
        body,
      )
    },
    [consume],
  )

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setStatus('idle')
    setSteps([])
    setError(null)
    setPaperId(null)
  }, [])

  return {
    status,
    steps,
    error,
    paperId,
    startArxivStream,
    startPdfStream,
    reset,
  }
}
