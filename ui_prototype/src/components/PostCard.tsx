import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Eye, Heart, MessageCircle, Share2, Star } from 'lucide-react';
import { Post } from '@/types';

interface PostCardProps {
  post: Post;
  onAnalyze?: (post: Post) => void;
  onViewDetails?: (post: Post) => void;
  isLoading?: boolean;
}

export const PostCard: React.FC<PostCardProps> = ({
  post,
  onAnalyze,
  onViewDetails,
  isLoading = false,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <Card className="w-full hover:shadow-md transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold truncate">
            {post.channel_title}
          </CardTitle>
          <Badge className={getStatusColor(post.status)}>
            {post.status}
          </Badge>
        </div>

        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center space-x-1">
            <Star className={`w-4 h-4 ${getScoreColor(post.score)}`} />
            <span className={getScoreColor(post.score)}>
              {post.score.toFixed(1)}
            </span>
          </div>

          <div className="flex items-center space-x-1">
            <Eye className="w-4 h-4" />
            <span>{formatNumber(post.views)}</span>
          </div>

          <div className="flex items-center space-x-1">
            <Heart className="w-4 h-4" />
            <span>{formatNumber(post.reactions)}</span>
          </div>

          <div className="flex items-center space-x-1">
            <MessageCircle className="w-4 h-4" />
            <span>{formatNumber(post.replies)}</span>
          </div>

          <div className="flex items-center space-x-1">
            <Share2 className="w-4 h-4" />
            <span>{formatNumber(post.forwards)}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-3">
          {/* Текст поста */}
          <div className="text-sm text-gray-800 leading-relaxed">
            <p className="line-clamp-3">
              {post.text.length > 200
                ? `${post.text.substring(0, 200)}...`
                : post.text
              }
            </p>
          </div>

          {/* Метрики вовлеченности */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-blue-50 rounded px-2 py-1">
              <span className="font-medium">ER:</span>{' '}
              {post.views > 0
                ? ((post.reactions + post.replies) / post.views * 100).toFixed(1)
                : 0
              }%
            </div>
            <div className="bg-green-50 rounded px-2 py-1">
              <span className="font-medium">Дата:</span>{' '}
              {new Date(post.created_at).toLocaleDateString('ru-RU')}
            </div>
          </div>

          {/* Кнопки действий */}
          <div className="flex space-x-2 pt-2">
            {onViewDetails && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onViewDetails(post)}
                className="flex-1"
              >
                Подробнее
              </Button>
            )}

            {onAnalyze && post.status !== 'processing' && (
              <Button
                size="sm"
                onClick={() => onAnalyze(post)}
                disabled={isLoading}
                className="flex-1"
              >
                {isLoading ? 'Обработка...' : 'Анализировать'}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
