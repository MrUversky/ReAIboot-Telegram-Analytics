import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Search,
  Filter,
  RefreshCw,
  BarChart3,
  FileText,
  Settings,
  Play,
  Zap
} from 'lucide-react';

import { PostCard } from '@/components/PostCard';
import { ScenarioCard } from '@/components/ScenarioCard';
import { AnalyticsDashboard } from '@/components/AnalyticsDashboard';
import { apiClient, handleApiResponse } from '@/lib/api';
import { Post, Scenario, AnalyticsData, FilterOptions } from '@/types';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('posts');
  const [posts, setPosts] = useState<Post[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<FilterOptions>({
    date_range: {
      start: '',
      end: '',
    },
    channels: [],
    score_range: {
      min: 0,
      max: 10,
    },
    status: [],
    sort_by: 'date',
    sort_order: 'desc',
  });

  // Загрузка данных при монтировании
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);

    try {
      // Загружаем посты
      const postsResponse = await handleApiResponse(
        () => apiClient.getPosts(filters)
      );
      if (postsResponse.data) {
        setPosts(postsResponse.data);
      }

      // Загружаем сценарии
      const scenariosResponse = await handleApiResponse(
        () => apiClient.getScenarios()
      );
      if (scenariosResponse.data) {
        setScenarios(scenariosResponse.data);
      }

      // Загружаем аналитику
      const analyticsResponse = await handleApiResponse(
        () => apiClient.getAnalytics()
      );
      if (analyticsResponse.data) {
        // Преобразуем данные в нужный формат
        setAnalytics({
          total_posts: analyticsResponse.data.total_posts || 0,
          processed_posts: analyticsResponse.data.processed_posts || 0,
          generated_scenarios: analyticsResponse.data.generated_scenarios || 0,
          avg_processing_time: analyticsResponse.data.avg_processing_time || 0,
          success_rate: analyticsResponse.data.success_rate || 0,
          cost_today: analyticsResponse.data.cost_today || 0,
          cost_month: analyticsResponse.data.cost_month || 0,
        });
      }
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzePost = async (post: Post) => {
    try {
      const response = await handleApiResponse(
        () => apiClient.processPosts([post])
      );

      if (response.data) {
        // Обновляем статус поста
        setPosts(prevPosts =>
          prevPosts.map(p =>
            p.id === post.id
              ? { ...p, status: 'processing' as const }
              : p
          )
        );

        // Перезагружаем данные через некоторое время
        setTimeout(() => loadData(), 2000);
      }
    } catch (error) {
      console.error('Ошибка анализа поста:', error);
    }
  };

  const handleEditScenario = (scenario: Scenario) => {
    // TODO: Открыть редактор сценария
    console.log('Редактирование сценария:', scenario.id);
  };

  const handleApproveScenario = async (scenario: Scenario) => {
    try {
      await apiClient.updateScenario(scenario.id, {
        ...scenario,
        status: 'approved'
      });
      loadData(); // Перезагрузка данных
    } catch (error) {
      console.error('Ошибка одобрения сценария:', error);
    }
  };

  const handlePublishScenario = async (scenario: Scenario) => {
    try {
      await apiClient.updateScenario(scenario.id, {
        ...scenario,
        status: 'published'
      });
      loadData(); // Перезагрузка данных
    } catch (error) {
      console.error('Ошибка публикации сценария:', error);
    }
  };

  // Фильтрация постов
  const filteredPosts = posts.filter(post => {
    const matchesSearch = searchQuery === '' ||
      post.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.channel_title.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesScore = post.score >= filters.score_range.min &&
      post.score <= filters.score_range.max;

    return matchesSearch && matchesScore;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                ReAIboot Dashboard
              </h1>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600">Система активна</span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={loadData}
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Обновить
              </Button>

              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4 mr-2" />
                Настройки
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview" className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4" />
              <span>Обзор</span>
            </TabsTrigger>
            <TabsTrigger value="posts" className="flex items-center space-x-2">
              <FileText className="w-4 h-4" />
              <span>Посты</span>
            </TabsTrigger>
            <TabsTrigger value="scenarios" className="flex items-center space-x-2">
              <Play className="w-4 h-4" />
              <span>Сценарии</span>
            </TabsTrigger>
            <TabsTrigger value="prompts" className="flex items-center space-x-2">
              <Zap className="w-4 h-4" />
              <span>Промпты</span>
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="mt-6">
            {analytics && (
              <AnalyticsDashboard data={analytics} isLoading={isLoading} />
            )}
          </TabsContent>

          {/* Posts Tab */}
          <TabsContent value="posts" className="mt-6">
            {/* Search and Filters */}
            <Card className="mb-6">
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="Поиск по тексту или каналу..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Select
                      value={filters.sort_by}
                      onValueChange={(value) =>
                        setFilters(prev => ({ ...prev, sort_by: value as any }))
                      }
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="date">По дате</SelectItem>
                        <SelectItem value="score">По рейтингу</SelectItem>
                        <SelectItem value="views">По просмотрам</SelectItem>
                      </SelectContent>
                    </Select>

                    <Button variant="outline" size="sm">
                      <Filter className="w-4 h-4 mr-2" />
                      Фильтры
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Posts Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredPosts.map((post) => (
                <PostCard
                  key={post.id}
                  post={post}
                  onAnalyze={handleAnalyzePost}
                  onViewDetails={(post) => console.log('View details:', post)}
                  isLoading={isLoading}
                />
              ))}
            </div>

            {filteredPosts.length === 0 && (
              <Card>
                <CardContent className="p-12 text-center">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Посты не найдены
                  </h3>
                  <p className="text-gray-500">
                    Попробуйте изменить поисковый запрос или фильтры
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Scenarios Tab */}
          <TabsContent value="scenarios" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {scenarios.map((scenario) => (
                <ScenarioCard
                  key={scenario.id}
                  scenario={scenario}
                  onEdit={handleEditScenario}
                  onApprove={handleApproveScenario}
                  onPublish={handlePublishScenario}
                />
              ))}
            </div>

            {scenarios.length === 0 && (
              <Card>
                <CardContent className="p-12 text-center">
                  <Play className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Сценарии не найдены
                  </h3>
                  <p className="text-gray-500">
                    Сначала проанализируйте посты, чтобы сгенерировать сценарии
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Prompts Tab */}
          <TabsContent value="prompts" className="mt-6">
            <Card>
              <CardContent className="p-12 text-center">
                <Zap className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Управление промптами
                </h3>
                <p className="text-gray-500 mb-4">
                  Здесь будет интерфейс для редактирования промптов LLM
                </p>
                <Button variant="outline">
                  Перейти к редактору промптов
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Dashboard;
