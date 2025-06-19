import graphene
from graphene_django import DjangoObjectType
from users.schema import UserType
from graphql import GraphQLError
from django.db.models import Q

from .models import Post, Reaction, Comment


# Tipo de objeto para Post (antes Tweet)
class PostType(DjangoObjectType):
    total_reactions = graphene.Int()
    comments = graphene.List(lambda: CommentType)
    comment_count = graphene.Int()
    reaction_count = graphene.Int()

    class Meta:
        model = Post

    def resolve_comment_count(self, info):
        return self.comments.count()

    def resolve_reaction_count(self, info):
        return self.reactions.count()

    def resolve_comments(self, info):
        return self.comments.all()
    
    def resolve_reactions(self, info):
        return self.reactions.all()


class ReactionType(DjangoObjectType):
    class Meta:
        model = Reaction


class CommentType(DjangoObjectType):
    class Meta:
        model = Comment


class Query(graphene.ObjectType):
    posts = graphene.List(
        PostType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
    )
    reactions = graphene.List(ReactionType)
    comments = graphene.List(CommentType, post_id=graphene.Int())

    def resolve_posts(self, info, search=None, first=None, skip=None, **kwargs):
        qs = Post.objects.all()
        if search:
            filter = (
                Q(nombre__icontains=search) |
                Q(modelo_helicoptero__icontains=search) |
                Q(descripcion__icontains=search)
            )
            qs = qs.filter(filter)
        if skip:
            qs = qs[skip:]
        if first:
            qs = qs[:first]
        return qs

    def resolve_reactions(self, info, **kwargs):
        return Reaction.objects.all()

    def resolve_comments(self, info, post_id=None, **kwargs):
        if post_id:
            return Comment.objects.filter(post__id=post_id)
        return Comment.objects.all()


class CreatePost(graphene.Mutation):
    post = graphene.Field(PostType)

    class Arguments:
        nombre = graphene.String(required=True)
        modelo_helicoptero = graphene.String(required=True)
        descripcion = graphene.String(required=True)
        url = graphene.String(required=False)

    def mutate(self, info, nombre, modelo_helicoptero, descripcion, url=None):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to create a post!")

        post = Post(
            nombre=nombre,
            modelo_helicoptero=modelo_helicoptero,
            descripcion=descripcion,
            url=url or "",
            posted_by=user
        )
        post.save()

        return CreatePost(post=post)


class CreateReaction(graphene.Mutation):
    reaction = graphene.Field(ReactionType)

    class Arguments:
        post_id = graphene.Int(required=True)
        reaction_type = graphene.String(required=True)

    def mutate(self, info, post_id, reaction_type):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to react!")

        post = Post.objects.filter(id=post_id).first()
        if not post:
            raise GraphQLError("Invalid Post!")

        existing_reaction = Reaction.objects.filter(user=user, post=post).first()

        if existing_reaction:
            existing_reaction.reaction_type = reaction_type
            existing_reaction.save()
            return CreateReaction(reaction=existing_reaction)
        else:
            reaction = Reaction.objects.create(
                user=user,
                post=post,
                reaction_type=reaction_type
            )
            return CreateReaction(reaction=reaction)


class CreateComment(graphene.Mutation):
    comment = graphene.Field(CommentType)

    class Arguments:
        post_id = graphene.Int(required=True)
        text = graphene.String(required=True)

    def mutate(self, info, post_id, text):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to comment!")

        post = Post.objects.filter(id=post_id).first()
        if not post:
            raise GraphQLError("Invalid Post!")

        comment = Comment.objects.create(
            user=user,
            post=post,
            text=text
        )

        return CreateComment(comment=comment)


class DeleteComment(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        comment_id = graphene.Int(required=True)

    def mutate(self, info, comment_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to delete a comment!")

        comment = Comment.objects.filter(id=comment_id, user=user).first()
        if not comment:
            raise GraphQLError("Comment not found or you are not the owner!")

        comment.delete()
        return DeleteComment(success=True)


class DeleteReaction(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        reaction_id = graphene.Int(required=True)

    def mutate(self, info, reaction_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to delete a reaction!")

        reaction = Reaction.objects.filter(id=reaction_id, user=user).first()
        if not reaction:
            raise GraphQLError("Reaction not found or you are not the owner!")

        reaction.delete()
        return DeleteReaction(success=True)


class DeletePost(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        post_id = graphene.Int(required=True)

    def mutate(self, info, post_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("You must be logged in to delete a post!")

        post = Post.objects.filter(id=post_id, posted_by=user).first()
        if not post:
            raise GraphQLError("Post not found or you are not the owner!")

        post.reactions.all().delete()
        post.comments.all().delete()
        post.delete()

        return DeletePost(success=True)


class Mutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    create_reaction = CreateReaction.Field()
    create_comment = CreateComment.Field()
    delete_comment = DeleteComment.Field()
    delete_reaction = DeleteReaction.Field()
    delete_post = DeletePost.Field()
