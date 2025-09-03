import React from 'react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Eye, Heart, MessageCircle, Share, ExternalLink, TrendingUp, Zap, BarChart3 } from 'lucide-react'
import type { Post } from '@/lib/api'

interface PostCardProps {
  post: Post
  onAnalyze?: (post: Post) => void
  showAnalysis?: boolean
}

export function PostCard({ post, onAnalyze, showAnalysis = true }: PostCardProps) {
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <Card className="w-full hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold line-clamp-2">
              {post.channel_title || `@${post.channel_username}`}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {formatDate(post.date)}
            </p>
          </div>
          {post.score && (
            <Badge variant="secondary" className="flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              {post.score.toFixed(2)}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        <p className="text-sm text-gray-700 line-clamp-4 mb-4">
          {post.text_preview}
        </p>

        {/* Metrics */}
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div className="flex items-center gap-2 text-sm">
            <Eye className="w-4 h-4 text-blue-500" />
            <span className="font-medium">{formatNumber(post.views)}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Heart className="w-4 h-4 text-red-500" />
            <span className="font-medium">{formatNumber(post.reactions)}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <MessageCircle className="w-4 h-4 text-green-500" />
            <span className="font-medium">{formatNumber(post.replies)}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Share className="w-4 h-4 text-purple-500" />
            <span className="font-medium">{formatNumber(post.forwards)}</span>
          </div>
        </div>

        {/* Viral Metrics */}
        {(post.viral_score !== undefined && post.viral_score !== null) && (
          <div className={`p-3 rounded-lg mb-4 ${
            (post.viral_score || 0) > 0
              ? 'bg-gradient-to-r from-purple-50 to-blue-50'
              : 'bg-gradient-to-r from-gray-50 to-gray-100'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              <Zap className={`w-4 h-4 ${(post.viral_score || 0) > 0 ? 'text-purple-600' : 'text-gray-500'}`} />
              <span className={`text-sm font-medium ${(post.viral_score || 0) > 0 ? 'text-gray-700' : 'text-gray-600'}`}>
                Виральные метрики
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <BarChart3 className={`w-3 h-3 ${(post.viral_score || 0) > 0 ? 'text-purple-500' : 'text-gray-400'}`} />
                <span className="text-gray-600">Viral Score:</span>
                <Badge variant={(post.viral_score || 0) >= 1.5 ? "default" : ((post.viral_score || 0) > 0 ? "secondary" : "outline")}>
                  {(post.viral_score || 0).toFixed(2)}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className={`w-3 h-3 ${(post.viral_score || 0) > 0 ? 'text-blue-500' : 'text-gray-400'}`} />
                <span className="text-gray-600">Engagement:</span>
                <span className={`font-medium ${(post.viral_score || 0) > 0 ? 'text-gray-900' : 'text-gray-500'}`}>
                  {((post.engagement_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
              {post.zscore !== undefined && post.zscore !== null && (
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">Z-score:</span>
                  <span className={`font-medium ${(post.viral_score || 0) > 0 ? 'text-gray-900' : 'text-gray-500'}`}>
                    {post.zscore.toFixed(2)}
                  </span>
                </div>
              )}
              {post.median_multiplier !== undefined && post.median_multiplier !== null && (
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">× медианы:</span>
                  <span className={`font-medium ${(post.viral_score || 0) > 0 ? 'text-gray-900' : 'text-gray-500'}`}>
                    {post.median_multiplier.toFixed(1)}×
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Rubrics */}
        {post.rubrics && post.rubrics.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-gray-600 mb-2">Подходящие рубрики:</p>
            <div className="flex flex-wrap gap-1">
              {post.rubrics.map((rubric, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {post.rubric_names?.[index] || rubric}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Media indicator */}
        {post.has_media && (
          <Badge variant="secondary" className="text-xs">
            📎 С медиа
          </Badge>
        )}
      </CardContent>

      <CardFooter className="pt-3 border-t">
        <div className="flex gap-2 w-full">
          <a
            href={post.permalink}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Открыть в TG
          </a>

          {showAnalysis && onAnalyze && (
            <Button
              size="sm"
              className="flex-1"
              onClick={() => onAnalyze(post)}
            >
              🤖 Анализировать
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  )
}
