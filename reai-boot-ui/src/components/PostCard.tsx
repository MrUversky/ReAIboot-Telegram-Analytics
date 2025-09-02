import React from 'react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Eye, Heart, MessageCircle, Share, ExternalLink, TrendingUp } from 'lucide-react'
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
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            asChild
          >
            <a
              href={post.permalink}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              Открыть в TG
            </a>
          </Button>

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
