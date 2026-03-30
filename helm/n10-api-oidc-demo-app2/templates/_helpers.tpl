{{- define "n10-api-oidc-demo-app2.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "n10-api-oidc-demo-app2.fullname" -}}
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

{{- define "n10-api-oidc-demo-app2.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "n10-api-oidc-demo-app2.labels" -}}
helm.sh/chart: {{ include "n10-api-oidc-demo-app2.chart" . }}
{{ include "n10-api-oidc-demo-app2.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "n10-api-oidc-demo-app2.selectorLabels" -}}
app.kubernetes.io/name: {{ include "n10-api-oidc-demo-app2.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
