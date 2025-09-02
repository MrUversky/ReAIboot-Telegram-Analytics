import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  TrendingUp,
  TrendingDown,
  Users,
  FileText,
  Clock,
  DollarSign,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { AnalyticsData } from '@/types';

interface AnalyticsDashboardProps {
  data: AnalyticsData;
  isLoading?: boolean;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  data,
  isLoading = false,
}) => {
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)} сек`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toFixed(0).padStart(2, '0')}`;
  };

  const metrics = [
    {
      title: 'Всего постов',
      value: formatNumber(data.total_posts),
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      trend: data.total_posts > 0 ? '+' : '0',
    },
    {
      title: 'Обработано',
      value: formatNumber(data.processed_posts),
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      trend: data.processed_posts > 0 ? '+' : '0',
    },
    {
      title: 'Сценариев',
      value: formatNumber(data.generated_scenarios),
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      trend: data.generated_scenarios > 0 ? '+' : '0',
    },
    {
      title: 'Среднее время',
      value: formatTime(data.avg_processing_time),
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      trend: data.avg_processing_time < 30 ? '↓' : '↑',
    },
  ];

  const costMetrics = [
    {
      title: 'Сегодня',
      value: `$${data.cost_today.toFixed(2)}`,
      icon: DollarSign,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    {
      title: 'Этот месяц',
      value: `$${data.cost_month.toFixed(2)}`,
      icon: DollarSign,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Основные метрики */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <Card key={index}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    {metric.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    {metric.value}
                  </p>
                </div>
                <div className={`p-3 rounded-full ${metric.bgColor}`}>
                  <metric.icon className={`w-6 h-6 ${metric.color}`} />
                </div>
              </div>
              <div className="mt-4">
                <div className="flex items-center text-sm">
                  {metric.trend.startsWith('+') ? (
                    <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                  ) : metric.trend.startsWith('↓') ? (
                    <TrendingDown className="w-4 h-4 text-green-500 mr-1" />
                  ) : null}
                  <span className="text-gray-500">{metric.trend}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Прогресс обработки */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            Прогресс обработки
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Обработано постов</span>
              <span className="text-sm text-gray-500">
                {data.processed_posts} из {data.total_posts}
              </span>
            </div>
            <Progress
              value={data.total_posts > 0 ? (data.processed_posts / data.total_posts) * 100 : 0}
              className="w-full"
            />
            <div className="text-xs text-gray-500">
              {((data.processed_posts / data.total_posts) * 100 || 0).toFixed(1)}% завершено
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Эффективность */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertCircle className="w-5 h-5 mr-2" />
              Эффективность системы
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm">Успешность обработки</span>
                <span className="text-sm font-medium">
                  {data.success_rate.toFixed(1)}%
                </span>
              </div>
              <Progress value={data.success_rate} className="w-full" />

              <div className="pt-2 space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Среднее время обработки</span>
                  <span>{formatTime(data.avg_processing_time)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Сценариев на пост</span>
                  <span>
                    {data.total_posts > 0
                      ? (data.generated_scenarios / data.total_posts).toFixed(1)
                      : '0'
                    }
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <DollarSign className="w-5 h-5 mr-2" />
              Стоимость использования
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {costMetrics.map((metric, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`p-2 rounded-full ${metric.bgColor} mr-3`}>
                      <metric.icon className={`w-4 h-4 ${metric.color}`} />
                    </div>
                    <span className="text-sm font-medium">{metric.title}</span>
                  </div>
                  <span className="text-lg font-bold">{metric.value}</span>
                </div>
              ))}

              <div className="pt-2 border-t">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Стоимость за пост</span>
                  <span>
                    ${data.total_posts > 0
                      ? (data.cost_today / data.total_posts).toFixed(3)
                      : '0.000'
                    }
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
