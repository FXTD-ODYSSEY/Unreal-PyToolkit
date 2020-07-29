// Copyright Epic Games, Inc. All Rights Reserved.

#include "PyToolkitBPLibrary.h"
#include "PyToolkit.h"
#include "MovieSceneTrack.h"


UPyToolkitBPLibrary::UPyToolkitBPLibrary(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{

}


ULevelSequence* UPyToolkitBPLibrary::GetFocusSequence()
{
	UAssetEditorSubsystem* sub = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
	TArray <UObject*> assets = sub->GetAllEditedAssets();

	for (UObject* asset : assets)
	{
		// Get LevelSequenceEditor

		IAssetEditorInstance* AssetEditor = sub->FindEditorForAsset(asset, false);
		FLevelSequenceEditorToolkit* LevelSequenceEditor = (FLevelSequenceEditorToolkit*)AssetEditor;

		if (LevelSequenceEditor != nullptr)
		{
			ULevelSequence* LevelSeq = Cast<ULevelSequence>(asset);
			return LevelSeq;
		}
	}

	return nullptr;
}

TArray<FGuid> UPyToolkitBPLibrary::GetFocusBindings(ULevelSequence* LevelSeq)
{
	IAssetEditorInstance* AssetEditor = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->FindEditorForAsset(LevelSeq, false);

	FLevelSequenceEditorToolkit* LevelSequenceEditor = (FLevelSequenceEditorToolkit*)AssetEditor;

	TArray<FGuid> SelectedGuid;
	if (LevelSequenceEditor != nullptr)
	{
		// Get current Sequencer
		ISequencer* Sequencer = LevelSequenceEditor->GetSequencer().Get();


		Sequencer->GetSelectedObjects(SelectedGuid);
		return SelectedGuid;
	}

	return SelectedGuid;
}

// https://forums.unrealengine.com/development-discussion/python-scripting/1703959-how-to-add-component-to-existing-actor-in-level-with-python-blueprint
//You pass to it class of component, otherwise it creates StaticMeshComponent
UActorComponent* UPyToolkitBPLibrary::AddComponent(AActor* a, USceneComponent *future_parent, FName name, UClass* NewComponentClass)
{

	UActorComponent* retComponent = nullptr;
	if (NewComponentClass)
	{
		UActorComponent* NewComponent = NewObject<UActorComponent>(a, NewComponentClass, name);
		FTransform CmpTransform;// = dup_source->GetComponentToWorld();
		//NewComponent->AttachToComponent(sc, FAttachmentTransformRules::KeepWorldTransform);
		// Do Scene Attachment if this new Comnponent is a USceneComponent
		if (USceneComponent* NewSceneComponent = Cast<USceneComponent>(NewComponent))
		{
			if (future_parent != 0)
				NewSceneComponent->AttachToComponent(future_parent, FAttachmentTransformRules::KeepWorldTransform);
			else
				NewSceneComponent->AttachToComponent(a->GetRootComponent(), FAttachmentTransformRules::KeepWorldTransform);

			NewSceneComponent->SetComponentToWorld(CmpTransform);
		}
		a->AddInstanceComponent(NewComponent);
		NewComponent->OnComponentCreated();
		NewComponent->RegisterComponent();

		a->RerunConstructionScripts();
		retComponent = NewComponent;
	}

	return retComponent;
}


UTextureCube* UPyToolkitBPLibrary::RenderTargetCubeCreateStaticTextureCube(UTextureRenderTargetCube* RenderTarget, FString InName)
{
	FString Name;
	FString PackageName;
	IAssetTools& AssetTools = FModuleManager::Get().LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();

	//Use asset name only if directories are specified, otherwise full path
	if (!InName.Contains(TEXT("/")))
	{
		FString AssetName = RenderTarget->GetOutermost()->GetName();
		const FString SanitizedBasePackageName = UPackageTools::SanitizePackageName(AssetName);
		const FString PackagePath = FPackageName::GetLongPackagePath(SanitizedBasePackageName) + TEXT("/");
		AssetTools.CreateUniqueAssetName(PackagePath, InName, PackageName, Name);
	}
	else
	{
		InName.RemoveFromStart(TEXT("/"));
		InName.RemoveFromStart(TEXT("Content/"));
		InName.StartsWith(TEXT("Game/")) == true ? InName.InsertAt(0, TEXT("/")) : InName.InsertAt(0, TEXT("/Game/"));
		AssetTools.CreateUniqueAssetName(InName, TEXT(""), PackageName, Name);
	}

	UTextureCube* NewTex = nullptr;

	// create a static 2d texture
	NewTex = RenderTarget->ConstructTextureCube(CreatePackage(NULL, *PackageName), Name, RenderTarget->GetMaskedFlags() | RF_Public | RF_Standalone);
	if (NewTex != nullptr)
	{
		// package needs saving
		NewTex->MarkPackageDirty();

		// Notify the asset registry
		FAssetRegistryModule::AssetCreated(NewTex);

	}
	return NewTex;

}


USkeletalMeshSocket* UPyToolkitBPLibrary::AddSkeletalMeshSocket(USkeleton* InSkeleton, FName InBoneName)
{
	USkeletalMeshSocket* socket = nullptr;

	ISkeletonEditorModule& SkeletonEditorModule = FModuleManager::LoadModuleChecked<ISkeletonEditorModule>("SkeletonEditor");
	TSharedRef<IEditableSkeleton> EditableSkeleton = SkeletonEditorModule.CreateEditableSkeleton(InSkeleton);
	socket = EditableSkeleton->AddSocket(InBoneName);
	return socket;
}

void UPyToolkitBPLibrary::DeleteSkeletalMeshSocket(USkeleton* InSkeleton, TArray<USkeletalMeshSocket*> SocketList)
{
	InSkeleton->Modify();
	for (USkeletalMeshSocket* Socket : SocketList)
	{
		InSkeleton->Sockets.Remove(Socket);
	}
	ISkeletonEditorModule& SkeletonEditorModule = FModuleManager::LoadModuleChecked<ISkeletonEditorModule>("SkeletonEditor");
	TSharedRef<IEditableSkeleton> EditableSkeleton = SkeletonEditorModule.CreateEditableSkeleton(InSkeleton);
	EditableSkeleton->RefreshBoneTree();
}

int32 UPyToolkitBPLibrary::GetSkeletonBoneNum(USkeleton* InSkeleton)
{
	return InSkeleton->GetReferenceSkeleton().GetNum();
}

FName UPyToolkitBPLibrary::GetSkeletonBoneName(USkeleton* InSkeleton,int32 BoneIndex)
{
	return InSkeleton->GetReferenceSkeleton().GetBoneName(BoneIndex);
}

