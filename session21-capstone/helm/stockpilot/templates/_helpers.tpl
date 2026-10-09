{{- define "sp.name" -}}{{ .Release.Name }}{{- end -}}

{{- define "sp.labels" -}}
app.kubernetes.io/part-of: stockpilot
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{/* selector labels for one component: include "sp.selector" (dict "ctx" . "component" "backend") */}}
{{- define "sp.selector" -}}
app.kubernetes.io/name: stockpilot-{{ .component }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
{{- end -}}

{{- define "sp.secretName" -}}
{{- if .Values.postgres.existingSecret -}}{{ .Values.postgres.existingSecret }}{{- else -}}{{ include "sp.name" . }}-db{{- end -}}
{{- end -}}

{{- define "sp.dbHost" -}}
{{- if .Values.postgres.enabled -}}{{ include "sp.name" . }}-postgres{{- else -}}{{ required "externalDatabase.host is required when postgres.enabled=false" .Values.externalDatabase.host }}{{- end -}}
{{- end -}}

{{- define "sp.podSecurity" -}}
runAsNonRoot: true
seccompProfile: { type: RuntimeDefault }
{{- end -}}

{{- define "sp.containerSecurity" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities: { drop: ["ALL"] }
{{- end -}}
