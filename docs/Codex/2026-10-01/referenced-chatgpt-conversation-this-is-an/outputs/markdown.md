# Markdown 작성 가이드

## 목차

1. [개요](#개요)
2. [기본 규칙](#기본-규칙)
3. [작성 예시](#작성-예시)
4. [실습 및 참고자료](#실습-및-참고자료)
5. [체크리스트](#체크리스트)

## 개요

Markdown은 제목, 목록, 링크, 코드 등을 간단한 기호로 표현하는 문서 형식입니다. 원본 `markdown_commands.md`에는 상세 문법 명령은 없고 학습용 참고 링크가 수록되어 있어 링크를 보존했습니다.

## 기본 규칙

```markdown
# 큰 제목
## 하위 제목

- 항목
- 항목

[링크 제목](https://example.com)

`인라인 코드`

```bash
명령어
```
```

셸 명령어와 문서 생성·편집 방법은 [Linux/Ubuntu 기본 명령어](linux_ubuntu.md)를 참고합니다. MkDocs로 게시하는 절차는 [MkDocs 가이드](mkdocs.md)에 정리했습니다.

## 작성 예시

````markdown
# 오늘의 학습

## 배운 내용

- `git status`로 변경 파일을 확인한다.
- 명령은 코드 블록으로 표시한다.

## 참고

[Git/GitHub 가이드](git_github.md)
````

## 실습 및 참고자료

원본 자료가 제공한 Markdown 학습 링크:

- [MarkDown 이해하기](https://velog.io/@roboticsmaster/%EA%B0%9C%EB%B0%9C%EA%B8%B0%EC%B4%88-Markdown%EC%9D%B4%ED%95%B4%ED%95%98%EA%B8%B0)

Git과 GitHub 관련 원본 참고 링크는 [참고자료 및 학습 링크](references.md)에 보존했습니다.

## 체크리스트

- [ ] 제목 계층을 순서대로 사용했다.
- [ ] 명령어와 코드는 코드 블록 또는 인라인 코드로 구분했다.
- [ ] 링크 텍스트만 보고도 목적을 알 수 있게 작성했다.
- [ ] 관련 주제 문서로 연결했다.
