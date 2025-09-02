import React, { useState } from 'react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import {
  ChevronDown,
  ChevronUp,
  Clock,
  Target,
  Lightbulb,
  Play,
  CheckCircle,
  Edit,
  Eye,
  Star
} from 'lucide-react'
import type { Scenario } from '@/lib/api'

interface ScenarioCardProps {
  scenario: Scenario
  onStatusUpdate?: (scenarioId: number, status: string) => void
  onEdit?: (scenario: Scenario) => void
}

export function ScenarioCard({ scenario, onStatusUpdate, onEdit }: ScenarioCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800'
      case 'approved': return 'bg-green-100 text-green-800'
      case 'published': return 'bg-blue-100 text-blue-800'
      case 'archived': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-4 h-4" />
      case 'published': return <Eye className="w-4 h-4" />
      default: return <Edit className="w-4 h-4" />
    }
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold line-clamp-2">
              {scenario.title}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {scenario.description}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={getStatusColor(scenario.status)}>
              {getStatusIcon(scenario.status)}
              <span className="ml-1 capitalize">{scenario.status}</span>
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-4 mt-3">
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Clock className="w-4 h-4" />
            <span>{scenario.duration_seconds} сек</span>
          </div>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Star className="w-4 h-4" />
            <span>Качество: {scenario.quality_score.toFixed(1)}</span>
          </div>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Target className="w-4 h-4" />
            <span>Охват: {scenario.engagement_prediction.toFixed(0)}%</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        {/* Hook */}
        {scenario.hook && scenario.hook.text && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-500">
            <div className="flex items-center gap-2 mb-2">
              <Play className="w-4 h-4 text-blue-600" />
              <h4 className="font-medium text-blue-900">Hook (Зацепка)</h4>
            </div>
            <p className="text-sm text-blue-800">{scenario.hook.text}</p>
          </div>
        )}

        {/* Insight */}
        {scenario.insight && scenario.insight.text && (
          <div className="mb-4 p-3 bg-green-50 rounded-lg border-l-4 border-green-500">
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb className="w-4 h-4 text-green-600" />
              <h4 className="font-medium text-green-900">Insight (Проникновение)</h4>
            </div>
            <p className="text-sm text-green-800">{scenario.insight.text}</p>
          </div>
        )}

        {/* Content preview */}
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          <CollapsibleTrigger asChild>
            <Button variant="outline" className="w-full justify-between">
              <span>Показать полный сценарий</span>
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
          </CollapsibleTrigger>

          <CollapsibleContent className="mt-4 space-y-4">
            {/* Main Content */}
            {scenario.content && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Основной контент</h4>
                <div className="text-sm text-gray-700 whitespace-pre-wrap">
                  {typeof scenario.content === 'string'
                    ? scenario.content
                    : JSON.stringify(scenario.content, null, 2)
                  }
                </div>
              </div>
            )}

            {/* Call to Action */}
            {scenario.call_to_action && scenario.call_to_action.text && (
              <div className="p-3 bg-purple-50 rounded-lg">
                <h4 className="font-medium text-purple-900 mb-2">Call to Action</h4>
                <p className="text-sm text-purple-800">{scenario.call_to_action.text}</p>
              </div>
            )}

            {/* Full scenario data */}
            {scenario.full_scenario && (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-800">
                  Полные данные сценария (JSON)
                </summary>
                <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-x-auto">
                  {JSON.stringify(scenario.full_scenario, null, 2)}
                </pre>
              </details>
            )}
          </CollapsibleContent>
        </Collapsible>
      </CardContent>

      <CardFooter className="pt-3 border-t">
        <div className="flex gap-2 w-full">
          {onEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(scenario)}
              className="flex-1"
            >
              <Edit className="w-4 h-4 mr-2" />
              Редактировать
            </Button>
          )}

          {onStatusUpdate && (
            <>
              {scenario.status === 'draft' && (
                <Button
                  size="sm"
                  onClick={() => onStatusUpdate(scenario.id, 'approved')}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Одобрить
                </Button>
              )}

              {scenario.status === 'approved' && (
                <Button
                  size="sm"
                  onClick={() => onStatusUpdate(scenario.id, 'published')}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  Опубликовать
                </Button>
              )}

              {scenario.status !== 'archived' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onStatusUpdate(scenario.id, 'archived')}
                  className="text-red-600 hover:text-red-700"
                >
                  Архив
                </Button>
              )}
            </>
          )}
        </div>
      </CardFooter>
    </Card>
  )
}
