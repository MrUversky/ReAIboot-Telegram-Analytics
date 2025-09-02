import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronRight, Play, Edit3, CheckCircle, Clock } from 'lucide-react';
import { Scenario } from '@/types';

interface ScenarioCardProps {
  scenario: Scenario;
  onEdit?: (scenario: Scenario) => void;
  onApprove?: (scenario: Scenario) => void;
  onPublish?: (scenario: Scenario) => void;
}

export const ScenarioCard: React.FC<ScenarioCardProps> = ({
  scenario,
  onEdit,
  onApprove,
  onPublish,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'bg-green-100 text-green-800';
      case 'approved':
        return 'bg-blue-100 text-blue-800';
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'published':
        return <CheckCircle className="w-4 h-4" />;
      case 'approved':
        return <CheckCircle className="w-4 h-4" />;
      case 'draft':
        return <Clock className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold truncate flex-1">
            {scenario.title}
          </CardTitle>
          <div className="flex items-center space-x-2 ml-4">
            <Badge className={getStatusColor(scenario.status)}>
              {getStatusIcon(scenario.status)}
              <span className="ml-1 capitalize">{scenario.status}</span>
            </Badge>
            <span className="text-sm text-gray-500">
              {scenario.duration} сек
            </span>
          </div>
        </div>

        <div className="text-sm text-gray-600">
          Создан: {new Date(scenario.created_at).toLocaleDateString('ru-RU')}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Hook */}
          <div className="bg-blue-50 rounded-lg p-3">
            <h4 className="font-medium text-blue-900 mb-2">🎣 Hook</h4>
            <p className="text-sm text-blue-800">
              {scenario.hook.text}
            </p>
            {scenario.hook.voiceover && (
              <p className="text-xs text-blue-600 mt-1 italic">
                🎤 {scenario.hook.voiceover}
              </p>
            )}
          </div>

          {/* Кнопка развертывания */}
          <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="w-full justify-between">
                <span>
                  {isExpanded ? 'Свернуть детали' : 'Показать детали'}
                </span>
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="space-y-4">
              {/* Insight */}
              <div className="bg-green-50 rounded-lg p-3">
                <h4 className="font-medium text-green-900 mb-2">💡 Insight</h4>
                <p className="text-sm text-green-800">
                  {scenario.insight.text}
                </p>
                {scenario.insight.voiceover && (
                  <p className="text-xs text-green-600 mt-1 italic">
                    🎤 {scenario.insight.voiceover}
                  </p>
                )}
              </div>

              {/* Steps */}
              {scenario.steps && scenario.steps.length > 0 && (
                <div className="bg-purple-50 rounded-lg p-3">
                  <h4 className="font-medium text-purple-900 mb-3">📋 Шаги</h4>
                  <div className="space-y-2">
                    {scenario.steps.map((step, index) => (
                      <div key={index} className="bg-white rounded p-2">
                        <div className="flex items-center justify-between mb-1">
                          <h5 className="font-medium text-sm">
                            Шаг {step.step}: {step.title}
                          </h5>
                          <span className="text-xs text-gray-500">
                            {step.duration} сек
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 mb-1">
                          {step.description}
                        </p>
                        {step.voiceover && (
                          <p className="text-xs text-gray-600 italic">
                            🎤 {step.voiceover}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* CTA */}
              <div className="bg-orange-50 rounded-lg p-3">
                <h4 className="font-medium text-orange-900 mb-2">🎯 CTA</h4>
                <p className="text-sm text-orange-800">
                  {scenario.cta.text}
                </p>
                {scenario.cta.voiceover && (
                  <p className="text-xs text-orange-600 mt-1 italic">
                    🎤 {scenario.cta.voiceover}
                  </p>
                )}
              </div>

              {/* Hashtags и музыка */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {scenario.hashtags && scenario.hashtags.length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <h4 className="font-medium text-gray-900 mb-2">🏷️ Хэштеги</h4>
                    <div className="flex flex-wrap gap-1">
                      {scenario.hashtags.map((tag, index) => (
                        <span
                          key={index}
                          className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {scenario.music_suggestion && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <h4 className="font-medium text-gray-900 mb-2">🎵 Музыка</h4>
                    <p className="text-sm text-gray-700">
                      {scenario.music_suggestion}
                    </p>
                  </div>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>

          {/* Кнопки действий */}
          <div className="flex space-x-2 pt-2">
            {onEdit && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEdit(scenario)}
                className="flex items-center space-x-1"
              >
                <Edit3 className="w-4 h-4" />
                <span>Редактировать</span>
              </Button>
            )}

            {onApprove && scenario.status === 'draft' && (
              <Button
                size="sm"
                onClick={() => onApprove(scenario)}
                className="flex items-center space-x-1 bg-green-600 hover:bg-green-700"
              >
                <CheckCircle className="w-4 h-4" />
                <span>Одобрить</span>
              </Button>
            )}

            {onPublish && scenario.status === 'approved' && (
              <Button
                size="sm"
                onClick={() => onPublish(scenario)}
                className="flex items-center space-x-1 bg-blue-600 hover:bg-blue-700"
              >
                <Play className="w-4 h-4" />
                <span>Опубликовать</span>
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
