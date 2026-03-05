# Dockerfile
FROM --platform=linux/amd64 golang:1.22-alpine AS build

# إعداد مجلد العمل
WORKDIR /app

# نسخ كل الملفات
COPY . .

# بناء التطبيق باسم notely
RUN go build -o notely main.go

# المرحلة الثانية: صورة أخف للتشغيل
FROM alpine:latest

# تثبيت شهادات SSL
RUN apk add --no-cache ca-certificates

# نسخ البرنامج المبني
COPY --from=build /app/notely /usr/bin/notely

# تشغيل البرنامج
CMD ["notely"]
