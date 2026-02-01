import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/$projectId/details')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/app/$projectId/details"!</div>
}
