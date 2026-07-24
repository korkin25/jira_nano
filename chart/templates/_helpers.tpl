{{/* Chart name (overridable). */}}
{{- define "jira-nano.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Fully qualified app name. */}}
{{- define "jira-nano.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "jira-nano.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "jira-nano.selectorLabels" -}}
app.kubernetes.io/name: {{ include "jira-nano.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "jira-nano.labels" -}}
helm.sh/chart: {{ include "jira-nano.chart" . }}
{{ include "jira-nano.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "jira-nano.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "jira-nano.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/* Fully-qualified image reference; empty tag falls back to appVersion. */}}
{{- define "jira-nano.image" -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- printf "%s:%s" .Values.image.repository $tag -}}
{{- end -}}

{{/* Voice model PVC name (created here unless an existingClaim is given). */}}
{{- define "jira-nano.voiceClaimName" -}}
{{- if .Values.voiceModel.existingClaim -}}
{{- .Values.voiceModel.existingClaim -}}
{{- else -}}
{{- printf "%s-models" (include "jira-nano.fullname" .) -}}
{{- end -}}
{{- end -}}
