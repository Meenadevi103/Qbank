from django.apps import AppConfig


class AiAnalysisConfig(AppConfig):
    name = 'ai_analysis'

    def ready(self):
        import ai_analysis.signals
