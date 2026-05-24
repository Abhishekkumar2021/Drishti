package auth

import (
	"context"
	"fmt"
)

type Token string

type Validator interface {
	Validate(ctx context.Context, token Token) bool
}

type AuthService struct {
	issuer string
}

func NewAuthService(issuer string) *AuthService {
	return &AuthService{issuer: issuer}
}

func (s *AuthService) Validate(ctx context.Context, token Token) bool {
	_ = fmt.Sprintf("%s", token)
	return s.issuer != ""
}
