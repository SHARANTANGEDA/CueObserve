import json
import dateutil.parser as dp
import datetime as dt
from rest_framework import serializers
from anomaly.models import Anomaly, AnomalyDefinition, Connection,ConnectionType, CustomSchedule as Schedule, Dataset, RunStatus, Setting


class ConnectionSerializer(serializers.ModelSerializer):
    connectionTypeId = serializers.SerializerMethodField()
    connectionType = serializers.SerializerMethodField()
    datasetCount = serializers.SerializerMethodField()


    def get_connectionTypeId(self, obj):
        return obj.connectionType.id

    def get_connectionType(self, obj):
        return obj.connectionType.name

    def get_datasetCount(self, obj):
        connectionId = obj.id
        datasetCount = Dataset.objects.filter(connection_id = connectionId).count()
        return datasetCount

    class Meta:
        model = Connection
        fields = [
            "id",
            "name",
            "description",
            "connectionTypeId",
            "connectionType",
            "datasetCount"
        ]


class ConnectionDetailSerializer(serializers.ModelSerializer):
    params = serializers.SerializerMethodField()
    connectionTypeId = serializers.SerializerMethodField()
    connectionType = serializers.SerializerMethodField()

    def get_params(self, obj):
        params = {}
        for val in obj.cpvc.all():
            params[val.connectionParam.name] = val.value if not val.connectionParam.isEncrypted else "**********"
        return params

    def get_connectionTypeId(self, obj):
        return obj.connectionType.id

    def get_connectionType(self, obj):
        return obj.connectionType.name

    class Meta:
        model = Connection
        fields = [
            "id",
            "name",
            "description",
            "params",
            "connectionTypeId",
            "connectionType",
        ]


class ConnectionTypeSerializer(serializers.ModelSerializer):
    
    params = serializers.SerializerMethodField()

    def get_params(self, obj):
        paramList = []
        for param in obj.connectionTypeParam.all():
            params = {}
            params["id"] = param.id
            params["name"] = param.name
            params["label"] = param.label
            params["isEncrypted"] = param.isEncrypted
            params["properties"] = param.properties
            paramList.append(params)
        return paramList

    class Meta:
        model = ConnectionType
        fields = ["id", "name", "params"]


class DatasetsSerializer(serializers.ModelSerializer):
    """
    Serializes data related to anomaly tree 
    """
    connection = ConnectionSerializer()
    anomalyDefinitionCount = serializers.SerializerMethodField()
    connectionName = serializers.SerializerMethodField()
    def get_connectionName(self, obj):
        """
        Gets connection name
        """
        return obj.connection.name

    def get_anomalyDefinitionCount(self, obj):
        """
        Gets anomaly definition count
        """
        return obj.anomalydefinition_set.count()

    class Meta:
        model = Dataset
        fields = ['id', 'name', 'granularity', 'connection', 'anomalyDefinitionCount',"connectionName"]


class DatasetSerializer(serializers.ModelSerializer):
    """
    Serializes data related to anomaly tree 
    """
    connection = ConnectionSerializer()
    dimensions = serializers.SerializerMethodField()
    metrics = serializers.SerializerMethodField()
    anomalyDefinitionCount = serializers.SerializerMethodField()

    def get_anomalyDefinitionCount(self, obj):
        """
        Gets anomaly definition count
        """
        return obj.anomalydefinition_set.count()

    def get_dimensions(self, obj):
        dimensions = json.loads(obj.dimensions) if obj.metrics else []
        return dimensions if dimensions else []

    def get_metrics(self, obj):
        metrics = json.loads(obj.metrics) if obj.metrics else []
        return metrics if metrics else []

    class Meta:
        model = Dataset
        fields = ['id', 'name', 'sql', 'connection', 'dimensions', 'metrics', 'granularity', 'timestampColumn', 'anomalyDefinitionCount']

class AnomalyDefinitionSerializer(serializers.ModelSerializer):
    """
    Serializes data related to anomlay Definition
    """
    anomalyDef = serializers.SerializerMethodField()
    schedule = serializers.SerializerMethodField()
    lastRun = serializers.SerializerMethodField()
    lastRunStatus = serializers.SerializerMethodField()
    lastRunAnomalies = serializers.SerializerMethodField()
    datasetName = serializers.SerializerMethodField()
    datasetGranularity = serializers.SerializerMethodField()
    
    def get_datasetName(self, obj):
        """
        Gets name of dataset
        """
        return obj.dataset.name

    def get_datasetGranularity(self, obj):
        """
        Gets granularity of dataset
        """
        return obj.dataset.granularity


    def get_anomalyDef(self, obj):
        params = {}
        params["id"] = obj.id
        params["metric"] = obj.metric
        params["dimension"] = obj.dimension
        params["highOrLow"] = obj.highOrLow
        params["operation"] = obj.operation
        params["value"] = obj.value
        return params

    def get_schedule(self, obj):
        name = None
        if obj.periodicTask:
            id = obj.periodicTask.crontab_id
            name = Schedule.objects.get(cronSchedule_id=id).name
        return name
    
    def get_lastRun(self, obj):
        runStatus = obj.runstatus_set.last()
        if runStatus:
            return runStatus.startTimestamp
    
    def get_lastRunStatus(self, obj):
        runStatus = obj.runstatus_set.last()
        if runStatus:
            return runStatus.status
    
    def get_lastRunAnomalies(self, obj):
        runStatus = obj.runstatus_set.last()
        if runStatus:
            runStatusObj = runStatus.logs
            runStatusObj["runStatusId"] = runStatus.id
            return runStatusObj

    
    class Meta:
        model = AnomalyDefinition
        fields = ["id",  "anomalyDef", "schedule", "lastRun", "lastRunStatus", "lastRunAnomalies", "datasetName", "datasetGranularity"]

class AnomalySerializer(serializers.ModelSerializer):
    """
    Serializes data for anomaly
    """
    datasetName = serializers.SerializerMethodField()
    granularity = serializers.SerializerMethodField()
    metric = serializers.SerializerMethodField()
    dimension = serializers.SerializerMethodField()

    def get_datasetName(self, obj):
        return obj.anomalyDefinition.dataset.name

    def get_granularity(self, obj):
        return obj.anomalyDefinition.dataset.granularity

    def get_metric(self, obj):
        return obj.anomalyDefinition.metric

    def get_dimension(self, obj):
        return obj.anomalyDefinition.dimension

    class Meta:
        model = Anomaly
        fields = ["id", "datasetName", "published", "dimension", "dimensionVal", "granularity", "metric", "data"]

class ScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for the model CrontabSchedule
    """
    schedule = serializers.SerializerMethodField()
    crontab = serializers.SerializerMethodField()
    timezone = serializers.SerializerMethodField()
    assignedSchedule = serializers.SerializerMethodField()

    def get_schedule(self, obj):
        """
        Gets string form of the crontab
        """
        return str(obj.cronSchedule)

    def get_timezone(self, obj):
        """ Gets schedule timezone"""
        return str(obj.cronSchedule.timezone)

    def cronexp(self, field):
        return field and str(field).replace(' ', '') or '*'
    
    def get_crontab(self, obj):
        """Gets schedule crontab """
        return '{0} {1} {2} {3} {4}'.format(
            self.cronexp(obj.cronSchedule.minute), self.cronexp(obj.cronSchedule.hour),
            self.cronexp(obj.cronSchedule.day_of_month), self.cronexp(obj.cronSchedule.month_of_year),
            self.cronexp(obj.cronSchedule.day_of_week)
        )

    def get_assignedSchedule(self, obj):
        """ Gets count of schedule assigned to Anomaly Definition"""
        cronId = Schedule.objects.get(id=obj.id).cronSchedule_id
        count = AnomalyDefinition.objects.filter(periodicTask__crontab_id=cronId).count()
        return count
    class Meta:
        model = Schedule
        fields = ["id", "schedule","name","timezone","crontab", "assignedSchedule"]

class RunStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for the model RunStatus
    """
    anomalyDefId = serializers.SerializerMethodField()

    def get_anomalyDefId(self, obj):
        """Gets AnomalyDefinition ID"""
        return obj.anomalyDefinition.id

    class Meta:
        model = RunStatus
        fields = ["id", "anomalyDefId", "startTimestamp", "endTimestamp", "status", "runType", "logs"]

class SettingSerializer(serializers.ModelSerializer):
    """
    Serializer for the model Setting
    """
    class Meta:
        model = Setting
        fields = ["name", "value"]
