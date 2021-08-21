// Copyright Epic Games, Inc. All Rights Reserved.

#include "PyToolkitBPLibrary.h"
#include "PyToolkit.h"

UPyToolkitBPLibrary::UPyToolkitBPLibrary(const FObjectInitializer &ObjectInitializer)
    : Super(ObjectInitializer)
{
}

#pragma region UnrealPythonLibrary
// copy from https://github.com/AlexQuevillon/UnrealPythonLibrary

TArray<UObject *> UPyToolkitBPLibrary::GetAllObjects()
{
    TArray<UObject *> Array;
    for (TObjectIterator<UObject> Itr; Itr; ++Itr)
    {
        Array.Add(*Itr);
    }
    return Array;
}

TArray<FString> UPyToolkitBPLibrary::GetAllProperties(UClass *Class)
{
    TArray<FString> Ret;
    if (Class != nullptr)
    {
        for (TFieldIterator<FProperty> It(Class); It; ++It)
        {
            FProperty *Property = *It;
            if (Property->HasAnyPropertyFlags(EPropertyFlags::CPF_Edit))
            {
                Ret.Add(Property->GetName());
            }
        }
    }
    return Ret;
}

void UPyToolkitBPLibrary::SetSelectedAssets(TArray<FString> Paths)
{
    FContentBrowserModule &ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
    FAssetRegistryModule &AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
    TArray<FName> PathsName;
    for (FString Path : Paths)
    {
        PathsName.Add(*Path);
    }
    FARFilter AssetFilter;
    AssetFilter.PackageNames = PathsName;
    TArray<FAssetData> AssetDatas;
    AssetRegistryModule.Get().GetAssets(AssetFilter, AssetDatas);
    ContentBrowserModule.Get().SyncBrowserToAssets(AssetDatas);
}

TArray<FString> UPyToolkitBPLibrary::GetSelectedFolders()
{
    FContentBrowserModule &ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
    TArray<FString> SelectedFolders;
    ContentBrowserModule.Get().GetSelectedFolders(SelectedFolders);
    return SelectedFolders;
}

void UPyToolkitBPLibrary::SetSelectedFolders(TArray<FString> Paths)
{
    FContentBrowserModule &ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
    ContentBrowserModule.Get().SyncBrowserToFolders(Paths);
}

void UPyToolkitBPLibrary::CloseEditorForAssets(TArray<UObject *> Assets)
{
    // NOTE 源码的方式已经过时，推荐用 SubSystem 的方式
    UAssetEditorSubsystem *sub = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
    for (UObject *Asset : Assets)
    {
        sub->CloseAllEditorsForAsset(Asset);
    }
}

TArray<UObject *> UPyToolkitBPLibrary::GetAssetsOpenedInEditor()
{
	UAssetEditorSubsystem *sub = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
	return sub->GetAllEditedAssets();
}

void UPyToolkitBPLibrary::SetFolderColor(FString FolderPath, FLinearColor Color)
{
    GConfig->SetString(TEXT("PathColor"), *FolderPath, *Color.ToString(), GEditorPerProjectIni);
}

int UPyToolkitBPLibrary::GetActiveViewportIndex()
{
    int Index = 1;
    if (GEditor != nullptr && GCurrentLevelEditingViewportClient != nullptr)
    {
        GEditor->GetLevelViewportClients().Find(GCurrentLevelEditingViewportClient, Index);
    }
    return Index;
}

// ViewportIndex is affected by the spawning order and not the viewport number.
//    e.g. Viewport 4 can be the first one if the user spawned it first.
//         And can become the last one if the user open the other ones and then close and re-open Viewport 4.
//    Also, the indexes are confusing.
// 1st Spawned Viewport : Index = 1
// 2nd Spawned Viewport : Index = 5
// 3rd Spawned Viewport : Index = 9
// 4th Spawned Viewport : Index = 13
void UPyToolkitBPLibrary::SetViewportLocationAndRotation(int ViewportIndex, FVector Location, FRotator Rotation)
{
    if (GEditor != nullptr && ViewportIndex < GEditor->GetLevelViewportClients().Num())
    {
        FLevelEditorViewportClient *LevelViewportClient = GEditor->GetLevelViewportClients()[ViewportIndex];
        if (LevelViewportClient != nullptr)
        {
            LevelViewportClient->SetViewLocation(Location);
            LevelViewportClient->SetViewRotation(Rotation);
        }
    }
}

#pragma endregion

#pragma region SequencerAPI


ULevelSequence *UPyToolkitBPLibrary::GetSequencerSequence()
{
    UAssetEditorSubsystem *sub = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
    TArray<UObject *> assets = sub->GetAllEditedAssets();

    for (UObject *asset : assets)
    {
        // Get LevelSequenceEditor

        IAssetEditorInstance *AssetEditor = sub->FindEditorForAsset(asset, false);
        FLevelSequenceEditorToolkit *LevelSequenceEditor = (FLevelSequenceEditorToolkit *)AssetEditor;

        if (LevelSequenceEditor != nullptr)
        {
            ULevelSequence *LevelSeq = Cast<ULevelSequence>(asset);
            return LevelSeq;
        }
    }

    return nullptr;
}

TArray<FGuid> UPyToolkitBPLibrary::GetSequencerSelectedID(ULevelSequence *LevelSeq)
{
    IAssetEditorInstance *AssetEditor = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->FindEditorForAsset(LevelSeq, false);

    FLevelSequenceEditorToolkit *LevelSequenceEditor = (FLevelSequenceEditorToolkit *)AssetEditor;

    TArray<FGuid> SelectedGuid;
    if (LevelSequenceEditor != nullptr)
    {
        // Get current Sequencer
        ISequencer *Sequencer = LevelSequenceEditor->GetSequencer().Get();

        Sequencer->GetSelectedObjects(SelectedGuid);
    }

    return SelectedGuid;
}

TArray<UMovieSceneTrack *> UPyToolkitBPLibrary::GetSequencerSelectedTracks(ULevelSequence *LevelSeq)
{
    IAssetEditorInstance *AssetEditor = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->FindEditorForAsset(LevelSeq, false);

    FLevelSequenceEditorToolkit *LevelSequenceEditor = (FLevelSequenceEditorToolkit *)AssetEditor;

    TArray<UMovieSceneTrack *> OutSelectedTracks;
    if (LevelSequenceEditor != nullptr)
    {
        // Get current Sequencer
        ISequencer *Sequencer = LevelSequenceEditor->GetSequencer().Get();

        Sequencer->GetSelectedTracks(OutSelectedTracks);
    }

    return OutSelectedTracks;
}

TSet<UMovieSceneSection *> UPyToolkitBPLibrary::GetSequencerSelectedSections(ULevelSequence *LevelSeq)
{
    IAssetEditorInstance *AssetEditor = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->FindEditorForAsset(LevelSeq, false);
    FLevelSequenceEditorToolkit *LevelSequenceEditor = (FLevelSequenceEditorToolkit *)AssetEditor;

    TArray<const IKeyArea *> KeyAreaArray;
    TSet<UMovieSceneSection *> OutSelectedSections;
    if (LevelSequenceEditor != nullptr)
    {
        ISequencer *Sequencer = LevelSequenceEditor->GetSequencer().Get();
        Sequencer->GetSelectedKeyAreas(KeyAreaArray);
        for (const IKeyArea *KeyArea : KeyAreaArray)
        {
            OutSelectedSections.Add(KeyArea->GetOwningSection());
        }
    }
    return OutSelectedSections;
}

TMap<UMovieSceneSection *, FString> UPyToolkitBPLibrary::GetSequencerSelectedChannels(ULevelSequence *LevelSeq)
{
    IAssetEditorInstance *AssetEditor = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->FindEditorForAsset(LevelSeq, false);
    FLevelSequenceEditorToolkit *LevelSequenceEditor = (FLevelSequenceEditorToolkit *)AssetEditor;

    TMap<UMovieSceneSection *, FString> OutMap;
    TArray<FString> KeyAreaNames;
    TArray<const IKeyArea *> KeyAreaArray;
    if (LevelSequenceEditor != nullptr)
    {
        ISequencer *Sequencer = LevelSequenceEditor->GetSequencer().Get();
        Sequencer->GetSelectedKeyAreas(KeyAreaArray);
        for (const IKeyArea *KeyArea : KeyAreaArray)
        {
            UMovieSceneSection *Section = KeyArea->GetOwningSection();
            if (OutMap.Contains(Section))
            {
                OutMap[Section] += "|" + KeyArea->GetName().ToString();
            }
            else
            {
                OutMap.Emplace(Section, KeyArea->GetName().ToString());
            }
            // KeyAreaNames.Add(KeyArea->GetName().ToString());
        }
    }
    return OutMap;
}

#pragma endregion

#pragma region SocketAPI

USkeletalMeshSocket *UPyToolkitBPLibrary::AddSkeletalMeshSocket(USkeleton *InSkeleton, FName InBoneName)
{
    USkeletalMeshSocket *socket = nullptr;

    ISkeletonEditorModule &SkeletonEditorModule = FModuleManager::LoadModuleChecked<ISkeletonEditorModule>("SkeletonEditor");
    TSharedRef<IEditableSkeleton> EditableSkeleton = SkeletonEditorModule.CreateEditableSkeleton(InSkeleton);
    socket = EditableSkeleton->AddSocket(InBoneName);
    return socket;
}

void UPyToolkitBPLibrary::DeleteSkeletalMeshSocket(USkeleton *InSkeleton, TArray<USkeletalMeshSocket *> SocketList)
{
    InSkeleton->Modify();
    for (USkeletalMeshSocket *Socket : SocketList)
    {
        InSkeleton->Sockets.Remove(Socket);
    }
    ISkeletonEditorModule &SkeletonEditorModule = FModuleManager::LoadModuleChecked<ISkeletonEditorModule>("SkeletonEditor");
    TSharedRef<IEditableSkeleton> EditableSkeleton = SkeletonEditorModule.CreateEditableSkeleton(InSkeleton);
    EditableSkeleton->RefreshBoneTree();
}

int32 UPyToolkitBPLibrary::GetSkeletonBoneNum(USkeleton *InSkeleton)
{
    return InSkeleton->GetReferenceSkeleton().GetNum();
}

FName UPyToolkitBPLibrary::GetSkeletonBoneName(USkeleton *InSkeleton, int32 BoneIndex)
{
    return InSkeleton->GetReferenceSkeleton().GetBoneName(BoneIndex);
}

#pragma endregion

#pragma region Material

UMaterialInstanceConstant *UPyToolkitBPLibrary::GetMaterialEditorSourceInstance(UMaterialEditorInstanceConstant *Editor)
{
    return Editor->SourceInstance;
}

void UPyToolkitBPLibrary::SetMaterialInstanceStaticSwitchParameterValue(UMaterialInstance *Instance, FName ParameterName, bool Value)
{
    FStaticParameterSet StaticParameters = Instance->GetStaticParameters();
    for (auto &SwitchParameter : StaticParameters.StaticSwitchParameters)
    {
        if (SwitchParameter.ParameterInfo.Name == ParameterName)
        {
            SwitchParameter.Value = Value;
            break;
            ;
        }
    }
    Instance->UpdateStaticPermutation(StaticParameters);
}

TArray<UMaterialExpression *> UPyToolkitBPLibrary::GetMaterialExpressions(UMaterial *Material)
{
    return Material->Expressions;
}

TArray<UMaterialExpression *> UPyToolkitBPLibrary::GetMaterialFunctionExpressions(UMaterialFunction *Function)
{
    return Function->FunctionExpressions;
}

#pragma endregion

#pragma region Msic

// https://forums.unrealengine.com/development-discussion/python-scripting/1703959-how-to-add-component-to-existing-actor-in-level-with-python-blueprint
//You pass to it class of component, otherwise it creates StaticMeshComponent
UActorComponent *UPyToolkitBPLibrary::AddComponent(AActor *a, USceneComponent *future_parent, FName name, UClass *NewComponentClass)
{

    UActorComponent *retComponent = nullptr;
    if (NewComponentClass)
    {
        UActorComponent *NewComponent = NewObject<UActorComponent>(a, NewComponentClass, name);
        FTransform CmpTransform; // = dup_source->GetComponentToWorld();
        //NewComponent->AttachToComponent(sc, FAttachmentTransformRules::KeepWorldTransform);
        // Do Scene Attachment if this new Comnponent is a USceneComponent
        if (USceneComponent *NewSceneComponent = Cast<USceneComponent>(NewComponent))
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

UTextureCube *UPyToolkitBPLibrary::RenderTargetCubeCreateStaticTextureCube(UTextureRenderTargetCube *RenderTarget, FString InName)
{
    FString Name;
    FString PackageName;
    IAssetTools &AssetTools = FModuleManager::Get().LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();

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

    UTextureCube *NewTex = nullptr;

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

FString UPyToolkitBPLibrary::GetCurrentContentPath()
{
    FContentBrowserModule &ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
    return ContentBrowserModule.Get().GetCurrentPath();
}


TArray<uint8> UPyToolkitBPLibrary::GetThumbnail(UObject* MeshObject,int32 _imageRes)
{
    // NOTE https://blog.csdn.net/zhangxiaofan666/article/details/97643308
    // int32 _imageRes = 128;
	FObjectThumbnail _objectThumnail;
	ThumbnailTools::RenderThumbnail(MeshObject, _imageRes, _imageRes, ThumbnailTools::EThumbnailTextureFlushMode::AlwaysFlush, NULL, &_objectThumnail);
	return _objectThumnail.GetUncompressedImageData();
}

bool UPyToolkitBPLibrary::ExecLevelEditorAction(FString Action)
{
    FLevelEditorModule &LevelEditorModule = FModuleManager::GetModuleChecked<FLevelEditorModule>(TEXT("LevelEditor"));
    auto Actions = LevelEditorModule.GetGlobalLevelEditorActions();
    auto Commands = LevelEditorModule.GetLevelEditorCommands();

    TMap<FString, TSharedPtr<FUICommandInfo>> ActionMap;

    ActionMap.Add("SaveAs", Commands.SaveAs);

    // Ctrl + E
    ActionMap.Add("EditAsset", Commands.EditAsset);
    // Ctrl + shift +  E
    ActionMap.Add("EditAssetNoConfirmMultiple", Commands.EditAssetNoConfirmMultiple);

    // Ctrl + End
    ActionMap.Add("SnapOriginToGrid", Commands.SnapOriginToGrid);
    ActionMap.Add("SnapOriginToGridPerActor", Commands.SnapOriginToGridPerActor);
    ActionMap.Add("AlignOriginToGrid", Commands.AlignOriginToGrid);
    // Ctrl + Space
    ActionMap.Add("SnapTo2DLayer", Commands.SnapTo2DLayer);
    // End
    ActionMap.Add("SnapToFloor", Commands.SnapToFloor);
    ActionMap.Add("AlignToFloor", Commands.AlignToFloor);
    // Alt + End
    ActionMap.Add("SnapPivotToFloor", Commands.SnapPivotToFloor);
    ActionMap.Add("AlignPivotToFloor", Commands.AlignPivotToFloor);
    // Shift + End
    ActionMap.Add("SnapBottomCenterBoundsToFloor", Commands.SnapBottomCenterBoundsToFloor);
    ActionMap.Add("AlignBottomCenterBoundsToFloor", Commands.AlignBottomCenterBoundsToFloor);

    ActionMap.Add("DeltaTransformToActors", Commands.DeltaTransformToActors);
    ActionMap.Add("MirrorActorX", Commands.MirrorActorX);
    ActionMap.Add("MirrorActorY", Commands.MirrorActorY);
    ActionMap.Add("MirrorActorZ", Commands.MirrorActorZ);
    ActionMap.Add("LockActorMovement", Commands.LockActorMovement);
    // alt + B
    ActionMap.Add("AttachSelectedActors", Commands.AttachSelectedActors);

    ActionMap.Add("SavePivotToPrePivot", Commands.SavePivotToPrePivot);
    ActionMap.Add("ResetPrePivot", Commands.ResetPrePivot);
    ActionMap.Add("ResetPivot", Commands.ResetPivot);
    ActionMap.Add("MovePivotHereSnapped", Commands.MovePivotHereSnapped);
    ActionMap.Add("MovePivotToCenter", Commands.MovePivotToCenter);

    ActionMap.Add("AlignToActor", Commands.AlignToActor);
    ActionMap.Add("AlignPivotToActor", Commands.AlignPivotToActor);

    ActionMap.Add("SelectAll", FGenericCommands::Get().SelectAll);
    // Escape
    ActionMap.Add("SelectNone", Commands.SelectNone);
    ActionMap.Add("InvertSelection", Commands.InvertSelection);
    // Ctrl + Alt + D
    ActionMap.Add("SelectImmediateChildren", Commands.SelectImmediateChildren);
    // Ctrl + Shift + D
    ActionMap.Add("SelectAllDescendants", Commands.SelectAllDescendants);

    ActionMap.Add("SelectRelevantLights", Commands.SelectRelevantLights);
    ActionMap.Add("SelectAllWithSameMaterial", Commands.SelectAllWithSameMaterial);

    // SLayersView.h
    bool Available = ActionMap.Contains(Action);
    if (Available)
    {
        auto ActionPtr = ActionMap[Action].ToSharedRef();
        Available = Actions->CanExecuteAction(ActionPtr);
        if (Available)
            Actions->ExecuteAction(ActionPtr);
    }
    return Available;
}

void UPyToolkitBPLibrary::RunFunction(UObject *CDO, UFunction *Function)
{
    // We dont run this on the CDO, as bad things could occur!
    UObject *TempObject = NewObject<UObject>(GetTransientPackage(), Cast<UObject>(CDO)->GetClass());
    TempObject->AddToRoot(); // Some Blutility actions might run GC so the TempObject needs to be rooted to avoid getting destroyed

    FScopedTransaction Transaction(NSLOCTEXT("UnrealEd", "BlutilityAction", "Blutility Action"));
    FEditorScriptExecutionGuard ScriptGuard;
    TempObject->ProcessEvent(Function, nullptr);
    TempObject->RemoveFromRoot();
}

#pragma endregion
